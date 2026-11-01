from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from datetime import date, datetime
import uuid
import logging

from app.database import get_db
from app.models.auth import User
from app.models.crm import Customer, Product
from app.models.projects import Order, Project
from app.models.finance import Invoice, InvoiceItem, Payment, PaymentAllocation
from app.models.workflow import AuditLog, Notification
from app.dependencies.auth import require_permissions, get_current_user
from app.utils.roles import SystemRole
from app.schemas import APIResponse
from app.schemas.finance import (
    InvoiceCreateRequest,
    InvoiceItemCreate,
    InvoiceItemResponse,
    InvoiceResponse,
    InvoiceListResponse,
    InvoiceCustomerSummary,
    InvoiceOrderSummary,
    InvoiceProjectSummary,
    PaymentAllocationCreateRequest,
    PaymentAllocationResponse,
    PaymentAllocationSummary,
    DirectInvoicePaymentRequest,
    PaymentRegisterItemResponse,
    PaymentRegisterListResponse,
    VALID_INVOICE_TYPES,
    VALID_INVOICE_STATUSES,
    VALID_PAYMENT_METHODS,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Finance & Billing"])


# ==========================================
# AUDIT & NOTIFICATION HELPERS
# ==========================================

def _record_audit_log(
    db: Session,
    user_id: Optional[int],
    action: str,
    entity_name: str,
    entity_id: int,
    details: Optional[dict] = None,
):
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_name=entity_name,
        entity_id=entity_id,
        details=details or {},
    )
    db.add(log)


def _send_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "FINANCE",
    link_url: Optional[str] = None,
):
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        link_url=link_url,
    )
    db.add(notif)


def _get_customer_for_user(user: User, db: Session) -> Optional[Customer]:
    return db.execute(select(Customer).where(Customer.user_id == user.id)).scalar_one_or_none()


def _build_invoice_response(inv: Invoice) -> InvoiceResponse:
    cust_summary = None
    if inv.customer:
        cust_summary = InvoiceCustomerSummary(
            id=inv.customer.id,
            full_name=inv.customer.full_name,
            phone=inv.customer.phone,
            email=inv.customer.email,
            city=inv.customer.city,
            state=inv.customer.state,
            pincode=inv.customer.pincode,
            address=inv.customer.address,
        )

    order_summary = None
    if inv.order:
        order_summary = InvoiceOrderSummary(
            id=inv.order.id,
            order_number=inv.order.order_number,
            order_date=inv.order.order_date,
            total_amount=Decimal(str(inv.order.total_amount)),
            advance_paid=Decimal(str(inv.order.advance_paid)),
            balance_amount=Decimal(str(inv.order.balance_amount)),
            status=inv.order.status,
        )

    proj_summary = None
    if inv.project:
        proj_summary = InvoiceProjectSummary(
            id=inv.project.id,
            project_code=inv.project.project_code,
            status=inv.project.status,
            system_capacity_kw=Decimal(str(inv.project.system_capacity_kw)),
            system_type=inv.project.system_type,
        )

    item_responses = []
    for it in (inv.items or []):
        item_responses.append(
            InvoiceItemResponse(
                id=it.id,
                invoice_id=it.invoice_id,
                product_id=it.product_id,
                product_code=it.product.product_code if it.product else None,
                product_name=it.product.name if it.product else None,
                item_description=it.item_description,
                quantity=Decimal(str(it.quantity)),
                unit_price=Decimal(str(it.unit_price)),
                tax_rate_percent=Decimal(str(it.tax_rate_percent)),
                total_amount=Decimal(str(it.total_amount)),
                created_at=it.created_at,
            )
        )

    allocation_responses = []
    for alloc in (inv.allocations or []):
        allocation_responses.append(
            PaymentAllocationResponse(
                id=alloc.id,
                payment_id=alloc.payment_id,
                payment_number=alloc.payment.payment_number if alloc.payment else "UNKNOWN",
                invoice_id=alloc.invoice_id,
                invoice_number=inv.invoice_number,
                allocated_amount=Decimal(str(alloc.allocated_amount)),
                allocated_at=alloc.allocated_at,
                created_at=alloc.created_at,
            )
        )

    return InvoiceResponse(
        id=inv.id,
        invoice_number=inv.invoice_number,
        order_id=inv.order_id,
        project_id=inv.project_id,
        customer_id=inv.customer_id,
        invoice_type=inv.invoice_type,
        invoice_date=inv.invoice_date,
        due_date=inv.due_date,
        subtotal=Decimal(str(inv.subtotal)),
        tax_amount=Decimal(str(inv.tax_amount)),
        total_amount=Decimal(str(inv.total_amount)),
        paid_amount=Decimal(str(inv.paid_amount)),
        balance_amount=Decimal(str(inv.balance_amount)),
        payment_status=inv.payment_status,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
        customer=cust_summary,
        order=order_summary,
        project=proj_summary,
        items=item_responses,
        allocations=allocation_responses,
    )


# ==========================================
# INVOICE ENDPOINTS
# ==========================================

@router.post("/invoices", response_model=APIResponse[InvoiceResponse], status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: InvoiceCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("invoices.create")),
):
    """
    Generate a customer advance, milestone, or final tax invoice against an order.
    Requires 'invoices.create' permission (held by SUPER_ADMIN, FINANCE_ACCOUNTS).
    Enforces that:
    1. Order must exist and not be CANCELLED.
    2. Optional project must match the order.
    3. Milestone cannot be duplicated for the same order.
    4. Invoice total cannot exceed remaining un-invoiced order contract balance.
    5. due_date >= invoice_date.
    6. Line items reference active catalog products and calculate subtotal/tax using Decimal.
    """
    # 1. Row-level lock on the target Order
    order = db.execute(
        select(Order)
        .options(
            selectinload(Order.customer),
            selectinload(Order.project),
        )
        .where(Order.id == payload.order_id)
        .with_for_update()
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {payload.order_id} not found.",
        )

    if order.status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot generate invoices for a CANCELLED order.",
        )

    # 2. Validate project if supplied
    if payload.project_id:
        proj = db.execute(
            select(Project).where(Project.id == payload.project_id)
        ).scalar_one_or_none()
        if not proj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {payload.project_id} not found.",
            )
        if proj.order_id != order.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project '{proj.project_code}' belongs to order ID {proj.order_id}, not order ID {order.id}.",
            )

    # 3. Enforce due_date >= invoice_date
    if payload.due_date < payload.invoice_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Due date ({payload.due_date}) cannot be earlier than invoice date ({payload.invoice_date}).",
        )

    # 4. Check for duplicate milestone billing on this order
    existing_milestone = db.execute(
        select(Invoice).where(
            Invoice.order_id == order.id,
            Invoice.invoice_type == payload.invoice_type,
        )
    ).first()

    if existing_milestone:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A milestone invoice of type '{payload.invoice_type}' has already been generated for order '{order.order_number}'. Duplicate milestone billing is rejected.",
        )

    # 5. Check order billing capacity (prior invoice total)
    prior_invoiced_total = db.execute(
        select(func.coalesce(func.sum(Invoice.total_amount), 0)).where(Invoice.order_id == order.id)
    ).scalar() or Decimal("0.00")
    prior_invoiced_total = Decimal(str(prior_invoiced_total))

    order_contract_limit = Decimal(str(order.total_amount))
    remaining_billable = order_contract_limit - prior_invoiced_total

    if remaining_billable <= Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order '{order.order_number}' is already fully invoiced (Total Contract: {order_contract_limit}, Invoiced: {prior_invoiced_total}).",
        )

    # 6. Process line items with authoritative Decimal calculation
    calculated_subtotal = Decimal("0.00")
    calculated_tax = Decimal("0.00")
    invoice_items_to_add = []

    for idx, it in enumerate(payload.items):
        if it.quantity <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Line item {idx + 1}: Quantity must be greater than zero.",
            )
        if it.unit_price < Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Line item {idx + 1}: Unit price cannot be negative.",
            )
        if it.tax_rate_percent < Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Line item {idx + 1}: Tax rate cannot be negative.",
            )

        prod = db.execute(select(Product).where(Product.id == it.product_id)).scalar_one_or_none()
        if not prod:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {it.product_id} not found in catalog.",
            )
        if not prod.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{prod.name}' ({prod.product_code}) is discontinued/inactive.",
            )

        line_desc = it.item_description.strip() if it.item_description else prod.name
        line_subtotal = (it.quantity * it.unit_price).quantize(Decimal("0.01"))
        line_tax = (line_subtotal * (it.tax_rate_percent / Decimal("100.00"))).quantize(Decimal("0.01"))
        line_total = line_subtotal + line_tax

        calculated_subtotal += line_subtotal
        calculated_tax += line_tax

        invoice_items_to_add.append({
            "product_id": prod.id,
            "item_description": line_desc,
            "quantity": it.quantity,
            "unit_price": it.unit_price,
            "tax_rate_percent": it.tax_rate_percent,
            "total_amount": line_total,
        })

    calculated_total = calculated_subtotal + calculated_tax

    # 7. Reconcile against remaining order contract value
    if calculated_total > remaining_billable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice total ({calculated_total}) exceeds remaining billable order limit ({remaining_billable}). Contract obligation cannot be over-invoiced.",
        )

    # 8. Build collision-resistant invoice number
    inv_number = f"INV-{date.today().year}{date.today().month:02d}-{uuid.uuid4().hex[:6].upper()}"

    invoice = Invoice(
        invoice_number=inv_number,
        order_id=order.id,
        project_id=payload.project_id or (order.project.id if order.project else None),
        customer_id=order.customer_id,
        invoice_type=payload.invoice_type,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        subtotal=calculated_subtotal,
        tax_amount=calculated_tax,
        total_amount=calculated_total,
        paid_amount=Decimal("0.00"),
        balance_amount=calculated_total,
        payment_status="PENDING",
    )
    db.add(invoice)

    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Database conflict while generating invoice: {str(exc.orig) if hasattr(exc, 'orig') else str(exc)}",
        )

    # 9. Insert line items
    for item_data in invoice_items_to_add:
        inv_item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=item_data["product_id"],
            item_description=item_data["item_description"],
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            tax_rate_percent=item_data["tax_rate_percent"],
            total_amount=item_data["total_amount"],
        )
        db.add(inv_item)

    # 10. Audit log
    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="INVOICE_CREATED",
        entity_name="INVOICE",
        entity_id=invoice.id,
        details={
            "invoice_number": invoice.invoice_number,
            "order_id": order.id,
            "order_number": order.order_number,
            "customer_id": order.customer_id,
            "invoice_type": invoice.invoice_type,
            "subtotal": float(calculated_subtotal),
            "tax_amount": float(calculated_tax),
            "total_amount": float(calculated_total),
            "due_date": str(payload.due_date),
        },
    )

    db.commit()
    db.expire_all()

    # Re-fetch with all eager relationships loaded
    loaded_inv = db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.customer),
            selectinload(Invoice.order),
            selectinload(Invoice.project),
            selectinload(Invoice.items).selectinload(InvoiceItem.product),
            selectinload(Invoice.allocations).selectinload(PaymentAllocation.payment),
        )
        .where(Invoice.id == invoice.id)
    ).scalar_one()

    return APIResponse(
        success=True,
        message=f"Invoice '{loaded_inv.invoice_number}' for INR {loaded_inv.total_amount} generated successfully.",
        data=_build_invoice_response(loaded_inv),
    )


@router.get("/invoices", response_model=APIResponse[InvoiceListResponse])
def list_invoices(
    search: Optional[str] = Query(None, description="Search by invoice number or customer name"),
    order_id: Optional[int] = Query(None, description="Filter by order ID"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    status: Optional[str] = Query(None, description="Filter by payment status (PENDING, PARTIALLY_PAID, PAID, OVERDUE)"),
    invoice_type: Optional[str] = Query(None, description="Filter by milestone invoice type"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("invoices.read")),
):
    """
    List commercial milestone tax invoices with filters and financial KPIs.
    Strictly applies customer data isolation: CUSTOMER role can only access their own invoices.
    """
    stmt = (
        select(Invoice)
        .options(
            selectinload(Invoice.customer),
            selectinload(Invoice.order),
            selectinload(Invoice.project),
            selectinload(Invoice.items).selectinload(InvoiceItem.product),
            selectinload(Invoice.allocations).selectinload(PaymentAllocation.payment),
        )
    )

    # Customer isolation
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        customer = _get_customer_for_user(current_user, db)
        if not customer:
            return APIResponse(
                success=True,
                message="No invoices found",
                data=InvoiceListResponse(
                    items=[], total=0, page=page, limit=limit, pages=0,
                    total_billed=Decimal("0.00"), total_paid=Decimal("0.00"), total_outstanding=Decimal("0.00"),
                ),
            )
        stmt = stmt.where(Invoice.customer_id == customer.id)
    elif customer_id:
        stmt = stmt.where(Invoice.customer_id == customer_id)

    if order_id:
        stmt = stmt.where(Invoice.order_id == order_id)

    if project_id:
        stmt = stmt.where(Invoice.project_id == project_id)

    if status:
        stmt = stmt.where(Invoice.payment_status == status.strip().upper())

    if invoice_type:
        stmt = stmt.where(Invoice.invoice_type == invoice_type.strip().upper())

    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.join(Invoice.customer).where(
            or_(
                Invoice.invoice_number.ilike(term),
                Customer.full_name.ilike(term),
                Customer.phone.ilike(term),
            )
        )

    # Count & KPI sums
    subq = stmt.subquery()
    count_stmt = select(func.count()).select_from(subq)
    total = db.execute(count_stmt).scalar() or 0

    sum_billed_stmt = select(func.coalesce(func.sum(subq.c.total_amount), 0))
    sum_paid_stmt = select(func.coalesce(func.sum(subq.c.paid_amount), 0))
    sum_bal_stmt = select(func.coalesce(func.sum(subq.c.balance_amount), 0))

    total_billed = Decimal(str(db.execute(sum_billed_stmt).scalar() or 0))
    total_paid = Decimal(str(db.execute(sum_paid_stmt).scalar() or 0))
    total_outstanding = Decimal(str(db.execute(sum_bal_stmt).scalar() or 0))

    offset = (page - 1) * limit
    invoices = db.execute(
        stmt.order_by(Invoice.created_at.desc()).offset(offset).limit(limit)
    ).scalars().all()

    pages = (total + limit - 1) // limit if total > 0 else 0
    items = [_build_invoice_response(inv) for inv in invoices]

    return APIResponse(
        success=True,
        message=f"Retrieved {len(items)} invoices.",
        data=InvoiceListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=pages,
            total_billed=total_billed,
            total_paid=total_paid,
            total_outstanding=total_outstanding,
        ),
    )


@router.get("/invoices/{id}", response_model=APIResponse[InvoiceResponse])
def get_invoice(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("invoices.read")),
):
    """
    Retrieve full invoice details with line items and linked payment allocations.
    Enforces customer ownership verification.
    """
    invoice = db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.customer),
            selectinload(Invoice.order),
            selectinload(Invoice.project),
            selectinload(Invoice.items).selectinload(InvoiceItem.product),
            selectinload(Invoice.allocations).selectinload(PaymentAllocation.payment),
        )
        .where(Invoice.id == id)
    ).scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {id} not found.",
        )

    # Customer isolation
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        customer = _get_customer_for_user(current_user, db)
        if not customer or invoice.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access invoices belonging to your own customer account.",
            )

    return APIResponse(
        success=True,
        message="Invoice retrieved successfully.",
        data=_build_invoice_response(invoice),
    )


@router.get("/orders/{id}/invoices", response_model=APIResponse[List[InvoiceResponse]])
def get_order_invoices(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("invoices.read")),
):
    """
    Retrieve all invoices associated with a specific customer Order.
    Enforces customer ownership.
    """
    order = db.execute(select(Order).where(Order.id == id)).scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {id} not found.",
        )

    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        customer = _get_customer_for_user(current_user, db)
        if not customer or order.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view invoices for your own orders.",
            )

    invoices = db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.customer),
            selectinload(Invoice.order),
            selectinload(Invoice.project),
            selectinload(Invoice.items).selectinload(InvoiceItem.product),
            selectinload(Invoice.allocations).selectinload(PaymentAllocation.payment),
        )
        .where(Invoice.order_id == id)
        .order_by(Invoice.invoice_date.asc())
    ).scalars().all()

    return APIResponse(
        success=True,
        message=f"Retrieved {len(invoices)} invoices for order '{order.order_number}'.",
        data=[_build_invoice_response(inv) for inv in invoices],
    )


# ==========================================
# PAYMENT ALLOCATION ENDPOINTS
# ==========================================

@router.post("/invoices/{id}/allocations", response_model=APIResponse[InvoiceResponse], status_code=status.HTTP_201_CREATED)
def allocate_payment_to_invoice(
    id: int,
    payload: PaymentAllocationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("payments.record")),
):
    """
    Allocate cash from an existing completed Payment receipt against an outstanding Invoice.
    Requires 'payments.record' permission (held by SUPER_ADMIN, FINANCE_ACCOUNTS).
    Enforces atomic row locking on both Invoice and Payment using SELECT FOR UPDATE.
    Reconciles available unallocated cash from actual payment allocation ledger history.
    """
    if payload.allocated_amount <= Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Allocated amount must be greater than zero.",
        )

    # 1. Lock Invoice row
    invoice = db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.customer),
            selectinload(Invoice.order),
            selectinload(Invoice.project),
            selectinload(Invoice.items).selectinload(InvoiceItem.product),
            selectinload(Invoice.allocations).selectinload(PaymentAllocation.payment),
        )
        .where(Invoice.id == id)
        .with_for_update()
    ).scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {id} not found.",
        )

    if invoice.balance_amount <= Decimal("0.00") or invoice.payment_status == "PAID":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice '{invoice.invoice_number}' is already fully paid.",
        )

    # 2. Lock Payment row
    payment = db.execute(
        select(Payment)
        .where(Payment.id == payload.payment_id)
        .with_for_update()
    ).scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with ID {payload.payment_id} not found.",
        )

    if payment.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment '{payment.payment_number}' is in status '{payment.status}'. Only COMPLETED payments can be allocated.",
        )

    # 3. Match customer and order consistency
    if payment.order_id != invoice.order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment '{payment.payment_number}' belongs to order ID {payment.order_id}, but invoice '{invoice.invoice_number}' belongs to order ID {invoice.order_id}.",
        )

    if payment.customer_id != invoice.customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment customer does not match invoice customer.",
        )

    # 4. Reconcile true available unallocated payment balance
    # Query actual allocation ledger sum for historical accuracy
    existing_allocated_sum = db.execute(
        select(func.coalesce(func.sum(PaymentAllocation.allocated_amount), 0))
        .where(PaymentAllocation.payment_id == payment.id)
    ).scalar() or Decimal("0.00")
    existing_allocated_sum = Decimal(str(existing_allocated_sum))

    payment_total = Decimal(str(payment.amount))
    effective_unallocated = payment_total - existing_allocated_sum

    if effective_unallocated <= Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment '{payment.payment_number}' has zero available unallocated balance (Total: {payment_total}, Allocated: {existing_allocated_sum}).",
        )

    if payload.allocated_amount > effective_unallocated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requested allocation amount ({payload.allocated_amount}) exceeds available payment balance ({effective_unallocated}).",
        )

    # 5. Guard against invoice over-allocation
    invoice_outstanding = Decimal(str(invoice.balance_amount))
    if payload.allocated_amount > invoice_outstanding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requested allocation amount ({payload.allocated_amount}) exceeds outstanding invoice balance ({invoice_outstanding}).",
        )

    # 6. Insert allocation record
    allocation = PaymentAllocation(
        payment_id=payment.id,
        invoice_id=invoice.id,
        allocated_amount=payload.allocated_amount,
    )
    db.add(allocation)

    # 7. Update balances
    new_unallocated = effective_unallocated - payload.allocated_amount
    payment.unallocated_amount = new_unallocated

    invoice.paid_amount = Decimal(str(invoice.paid_amount)) + payload.allocated_amount
    invoice.balance_amount = Decimal(str(invoice.total_amount)) - invoice.paid_amount

    if invoice.balance_amount <= Decimal("0.00"):
        invoice.payment_status = "PAID"
    else:
        invoice.payment_status = "PARTIALLY_PAID"

    # 8. Audit log
    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="PAYMENT_ALLOCATED",
        entity_name="PAYMENT_ALLOCATION",
        entity_id=payment.id,
        details={
            "payment_id": payment.id,
            "payment_number": payment.payment_number,
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "allocated_amount": float(payload.allocated_amount),
            "new_payment_unallocated": float(payment.unallocated_amount),
            "new_invoice_balance": float(invoice.balance_amount),
            "invoice_status": invoice.payment_status,
        },
    )

    db.commit()
    db.expire_all()

    # Re-fetch invoice with updated allocations
    refreshed_inv = db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.customer),
            selectinload(Invoice.order),
            selectinload(Invoice.project),
            selectinload(Invoice.items).selectinload(InvoiceItem.product),
            selectinload(Invoice.allocations).selectinload(PaymentAllocation.payment),
        )
        .where(Invoice.id == invoice.id)
    ).scalar_one()

    return APIResponse(
        success=True,
        message=f"INR {payload.allocated_amount} allocated to invoice '{refreshed_inv.invoice_number}'. New invoice balance: INR {refreshed_inv.balance_amount}.",
        data=_build_invoice_response(refreshed_inv),
    )


# ==========================================
# DIRECT INVOICE PAYMENT ENDPOINT
# ==========================================

@router.post("/invoices/{id}/payments", response_model=APIResponse[InvoiceResponse], status_code=status.HTTP_201_CREATED)
def record_direct_invoice_payment(
    id: int,
    payload: DirectInvoicePaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("payments.record")),
):
    """
    Directly record a customer payment against an outstanding Invoice.
    Creates a Payment receipt on the Order and a PaymentAllocation to the Invoice in the same atomic transaction.
    Reconciles both Order advance/balance amounts and Invoice paid/balance amounts exactly once.
    """
    if payload.amount <= Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be greater than zero.",
        )

    # 1. Lock Invoice row
    invoice = db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.customer),
            selectinload(Invoice.order),
            selectinload(Invoice.project),
            selectinload(Invoice.items).selectinload(InvoiceItem.product),
            selectinload(Invoice.allocations).selectinload(PaymentAllocation.payment),
        )
        .where(Invoice.id == id)
        .with_for_update()
    ).scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with ID {id} not found.",
        )

    if invoice.balance_amount <= Decimal("0.00") or invoice.payment_status == "PAID":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice '{invoice.invoice_number}' is already fully paid.",
        )

    if payload.amount > invoice.balance_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment amount ({payload.amount}) exceeds outstanding invoice balance ({invoice.balance_amount}). Overpayment is not permitted.",
        )

    # 2. Lock Order row
    order = db.execute(
        select(Order).where(Order.id == invoice.order_id).with_for_update()
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated order not found.",
        )

    if order.status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot record payment against a CANCELLED order.",
        )

    # Check transaction_reference uniqueness if provided
    if payload.transaction_reference:
        existing_ref = db.execute(
            select(Payment).where(Payment.transaction_reference == payload.transaction_reference.strip())
        ).scalar_one_or_none()
        if existing_ref:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Transaction reference '{payload.transaction_reference}' has already been recorded for payment '{existing_ref.payment_number}'.",
            )

    # 3. Create Payment receipt on order
    pay_number = f"PAY-{date.today().year}-{uuid.uuid4().hex[:6].upper()}"
    payment = Payment(
        payment_number=pay_number,
        customer_id=order.customer_id,
        order_id=order.id,
        project_id=invoice.project_id or (order.project.id if order.project else None),
        payment_date=payload.payment_date or date.today(),
        payment_method=payload.payment_method,
        transaction_reference=payload.transaction_reference.strip() if payload.transaction_reference else None,
        amount=payload.amount,
        unallocated_amount=Decimal("0.00"),  # Fully allocated to this invoice immediately
        status="COMPLETED",
        notes=payload.notes or f"Direct payment towards invoice {invoice.invoice_number}",
        received_by=current_user.id,
    )
    db.add(payment)

    try:
        db.flush()  # Allocate payment.id
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Database integrity error while recording payment: {str(exc.orig) if hasattr(exc, 'orig') else str(exc)}",
        )

    # 4. Create PaymentAllocation linking Payment to Invoice
    allocation = PaymentAllocation(
        payment_id=payment.id,
        invoice_id=invoice.id,
        allocated_amount=payload.amount,
    )
    db.add(allocation)

    # 5. Update Order balances
    order.advance_paid = Decimal(str(order.advance_paid)) + payload.amount
    order.balance_amount = Decimal(str(order.total_amount)) - order.advance_paid

    if order.status == "PENDING_ADVANCE":
        order.status = "CONFIRMED"

    # 6. Update Invoice balances
    invoice.paid_amount = Decimal(str(invoice.paid_amount)) + payload.amount
    invoice.balance_amount = Decimal(str(invoice.total_amount)) - invoice.paid_amount

    if invoice.balance_amount <= Decimal("0.00"):
        invoice.payment_status = "PAID"
    else:
        invoice.payment_status = "PARTIALLY_PAID"

    # 7. Audit log
    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="INVOICE_PAYMENT_RECORDED",
        entity_name="INVOICE",
        entity_id=invoice.id,
        details={
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "payment_id": payment.id,
            "payment_number": payment.payment_number,
            "amount": float(payload.amount),
            "payment_method": payload.payment_method,
            "invoice_balance": float(invoice.balance_amount),
            "order_balance": float(order.balance_amount),
        },
    )

    db.commit()
    db.expire_all()

    refreshed_inv = db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.customer),
            selectinload(Invoice.order),
            selectinload(Invoice.project),
            selectinload(Invoice.items).selectinload(InvoiceItem.product),
            selectinload(Invoice.allocations).selectinload(PaymentAllocation.payment),
        )
        .where(Invoice.id == invoice.id)
    ).scalar_one()

    return APIResponse(
        success=True,
        message=f"Payment '{payment.payment_number}' of INR {payload.amount} recorded and allocated to invoice '{refreshed_inv.invoice_number}'.",
        data=_build_invoice_response(refreshed_inv),
    )


# ==========================================
# PAYMENT REGISTER ENDPOINT
# ==========================================

@router.get("/payments", response_model=APIResponse[PaymentRegisterListResponse])
def list_payments(
    search: Optional[str] = Query(None, description="Search by payment number or customer name"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    order_id: Optional[int] = Query(None, description="Filter by order ID"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    status: Optional[str] = Query(None, description="Filter by payment status (COMPLETED, PENDING, FAILED, REFUNDED)"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method (UPI, NEFT, etc.)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("payments.read")),
):
    """
    List all customer payment receipts with allocation history and available unallocated balances.
    Strictly enforces customer isolation: CUSTOMER users only see their own payment receipts.
    """
    stmt = (
        select(Payment)
        .options(
            selectinload(Payment.customer),
            selectinload(Payment.order),
            selectinload(Payment.project),
            selectinload(Payment.receiver),
            selectinload(Payment.allocations).selectinload(PaymentAllocation.invoice),
        )
    )

    # Customer isolation
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        customer = _get_customer_for_user(current_user, db)
        if not customer:
            return APIResponse(
                success=True,
                message="No payments found",
                data=PaymentRegisterListResponse(
                    items=[], total=0, page=page, limit=limit, pages=0,
                    total_collected=Decimal("0.00"), total_unallocated=Decimal("0.00"),
                ),
            )
        stmt = stmt.where(Payment.customer_id == customer.id)
    elif customer_id:
        stmt = stmt.where(Payment.customer_id == customer_id)

    if order_id:
        stmt = stmt.where(Payment.order_id == order_id)

    if project_id:
        stmt = stmt.where(Payment.project_id == project_id)

    if status:
        stmt = stmt.where(Payment.status == status.strip().upper())

    if payment_method:
        stmt = stmt.where(Payment.payment_method == payment_method.strip().upper())

    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.join(Payment.customer).where(
            or_(
                Payment.payment_number.ilike(term),
                Payment.transaction_reference.ilike(term),
                Customer.full_name.ilike(term),
            )
        )

    subq = stmt.subquery()
    count_stmt = select(func.count()).select_from(subq)
    total = db.execute(count_stmt).scalar() or 0

    sum_amt_stmt = select(func.coalesce(func.sum(subq.c.amount), 0))
    sum_unalloc_stmt = select(func.coalesce(func.sum(subq.c.unallocated_amount), 0))

    total_collected = Decimal(str(db.execute(sum_amt_stmt).scalar() or 0))
    total_unallocated = Decimal(str(db.execute(sum_unalloc_stmt).scalar() or 0))

    offset = (page - 1) * limit
    payments = db.execute(
        stmt.order_by(Payment.created_at.desc()).offset(offset).limit(limit)
    ).scalars().all()

    pages = (total + limit - 1) // limit if total > 0 else 0

    item_list = []
    for p in payments:
        alloc_summaries = [
            PaymentAllocationSummary(
                id=al.id,
                invoice_id=al.invoice_id,
                invoice_number=al.invoice.invoice_number if al.invoice else "UNKNOWN",
                allocated_amount=Decimal(str(al.allocated_amount)),
                allocated_at=al.allocated_at,
            )
            for al in (p.allocations or [])
        ]

        item_list.append(
            PaymentRegisterItemResponse(
                id=p.id,
                payment_number=p.payment_number,
                customer_id=p.customer_id,
                customer_name=p.customer.full_name if p.customer else None,
                order_id=p.order_id,
                order_number=p.order.order_number if p.order else None,
                project_id=p.project_id,
                project_code=p.project.project_code if p.project else None,
                payment_date=p.payment_date,
                payment_method=p.payment_method,
                transaction_reference=p.transaction_reference,
                amount=Decimal(str(p.amount)),
                unallocated_amount=Decimal(str(p.unallocated_amount)),
                status=p.status,
                notes=p.notes,
                received_by=p.received_by,
                receiver_name=p.receiver.full_name if p.receiver else None,
                created_at=p.created_at,
                allocations=alloc_summaries,
            )
        )

    return APIResponse(
        success=True,
        message=f"Retrieved {len(item_list)} payments.",
        data=PaymentRegisterListResponse(
            items=item_list,
            total=total,
            page=page,
            limit=limit,
            pages=pages,
            total_collected=total_collected,
            total_unallocated=total_unallocated,
        ),
    )
