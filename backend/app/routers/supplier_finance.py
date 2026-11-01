from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_, desc
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
import math

from app.database import get_db
from app.models.auth import User, Role
from app.models.workflow import AuditLog
from app.models.crm import Customer, Product
from app.models.projects import (
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
    SupplierInvoice,
    SupplierPayment,
    SupplierPaymentAllocation,
    Order,
    Project,
    ProjectBomItem,
)
from app.models.finance import (
    Invoice,
    Payment,
    Expense,
    ProjectCost,
)
from app.schemas.supplier_finance import (
    SupplierInvoiceCreate,
    SupplierInvoiceStatusUpdate,
    SupplierInvoiceResponse,
    SupplierInvoiceDetailResponse,
    SupplierInvoicePaymentAllocationResponse,
    SupplierPaymentCreate,
    SupplierPaymentAllocationCreate,
    DirectSupplierInvoicePaymentCreate,
    SupplierPaymentResponse,
    ProjectCostCreate,
    ProjectCostResponse,
    ProjectProfitabilityResponse,
    VALID_SUPPLIER_INVOICE_STATUSES,
    VALID_PAYMENT_MODES,
    VALID_COST_CATEGORIES,
)
from app.schemas import APIResponse
from app.dependencies.auth import get_current_user, get_user_permissions
from app.utils.roles import SystemRole

router = APIRouter(tags=["Accounts Payable & Supplier Finance"])


# ==========================================
# INTERNAL HELPERS & AUTHORIZATION
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


def require_ap_access(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role and current_user.role.slug in {
        SystemRole.SUPER_ADMIN,
        SystemRole.DIRECTOR,
        SystemRole.FINANCE_ACCOUNTS,
        SystemRole.WAREHOUSE_PROCUREMENT,
    }:
        return current_user
    raise HTTPException(status_code=403, detail="Unauthorized to access accounts payable operations")


def require_finance_manager(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role and current_user.role.slug in {
        SystemRole.SUPER_ADMIN,
        SystemRole.DIRECTOR,
        SystemRole.FINANCE_ACCOUNTS,
    }:
        return current_user
    raise HTTPException(status_code=403, detail="Finance manager permission required for payments and allocations")


def _generate_supplier_payment_ref(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"SPAY-{year}-"
    latest = (
        db.execute(
            select(SupplierPayment.payment_reference)
            .where(SupplierPayment.payment_reference.like(f"{prefix}%"))
            .order_by(SupplierPayment.payment_reference.desc())
            .with_for_update()
        )
        .scalars()
        .first()
    )
    if latest:
        try:
            seq = int(latest.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


# ==========================================
# 1. SUPPLIER INVOICES (AP BILLS)
# ==========================================

@router.get("/supplier-invoices", response_model=APIResponse[dict])
def list_supplier_invoices(
    supplier_id: Optional[int] = Query(None),
    purchase_order_id: Optional[int] = Query(None),
    payment_status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_ap_access),
    db: Session = Depends(get_db),
):
    query = (
        select(SupplierInvoice)
        .options(
            selectinload(SupplierInvoice.supplier),
            selectinload(SupplierInvoice.purchase_order),
        )
    )

    if supplier_id:
        query = query.where(SupplierInvoice.supplier_id == supplier_id)
    if purchase_order_id:
        query = query.where(SupplierInvoice.purchase_order_id == purchase_order_id)
    if payment_status:
        query = query.where(SupplierInvoice.payment_status == payment_status.strip().upper())

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0

    invoices = (
        db.execute(
            query.order_by(SupplierInvoice.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    items = []
    for inv in invoices:
        po = inv.purchase_order
        variance = (inv.total_amount - po.total_amount) if po else Decimal("0.00")
        items.append(
            SupplierInvoiceResponse(
                id=inv.id,
                invoice_number=inv.invoice_number,
                purchase_order_id=inv.purchase_order_id,
                po_number=po.po_number if po else None,
                po_total=po.total_amount if po else None,
                supplier_id=inv.supplier_id,
                supplier_name=inv.supplier.company_name if inv.supplier else None,
                supplier_gstin=inv.supplier.gst_number if inv.supplier else None,
                invoice_date=inv.invoice_date,
                due_date=inv.due_date,
                subtotal=inv.subtotal,
                tax_amount=inv.tax_amount,
                total_amount=inv.total_amount,
                paid_amount=inv.paid_amount,
                balance_amount=inv.balance_amount,
                payment_status=inv.payment_status,
                variance_amount=variance,
                created_at=inv.created_at,
                updated_at=inv.updated_at,
            )
        )

    return APIResponse(
        message="Supplier invoices retrieved",
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        },
    )


@router.get("/supplier-invoices/{id}", response_model=APIResponse[SupplierInvoiceDetailResponse])
def get_supplier_invoice(
    id: int,
    current_user: User = Depends(require_ap_access),
    db: Session = Depends(get_db),
):
    inv = (
        db.execute(
            select(SupplierInvoice)
            .options(
                selectinload(SupplierInvoice.supplier),
                selectinload(SupplierInvoice.purchase_order),
                selectinload(SupplierInvoice.allocations).selectinload(SupplierPaymentAllocation.supplier_payment),
            )
            .where(SupplierInvoice.id == id)
        )
        .scalars()
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Supplier invoice not found")

    po = inv.purchase_order
    variance = (inv.total_amount - po.total_amount) if po else Decimal("0.00")

    allocations_resp = [
        SupplierInvoicePaymentAllocationResponse(
            id=a.id,
            supplier_payment_id=a.supplier_payment_id,
            supplier_invoice_id=a.supplier_invoice_id,
            payment_reference=a.supplier_payment.payment_reference if a.supplier_payment else None,
            allocated_amount=a.allocated_amount,
            allocated_at=a.allocated_at,
        )
        for a in (inv.allocations or [])
    ]

    return APIResponse(
        message="Supplier invoice details retrieved",
        data=SupplierInvoiceDetailResponse(
            id=inv.id,
            invoice_number=inv.invoice_number,
            purchase_order_id=inv.purchase_order_id,
            po_number=po.po_number if po else None,
            po_total=po.total_amount if po else None,
            supplier_id=inv.supplier_id,
            supplier_name=inv.supplier.company_name if inv.supplier else None,
            supplier_gstin=inv.supplier.gst_number if inv.supplier else None,
            invoice_date=inv.invoice_date,
            due_date=inv.due_date,
            subtotal=inv.subtotal,
            tax_amount=inv.tax_amount,
            total_amount=inv.total_amount,
            paid_amount=inv.paid_amount,
            balance_amount=inv.balance_amount,
            payment_status=inv.payment_status,
            variance_amount=variance,
            created_at=inv.created_at,
            updated_at=inv.updated_at,
            allocations=allocations_resp,
        ),
    )


@router.post("/supplier-invoices", response_model=APIResponse[SupplierInvoiceResponse], status_code=status.HTTP_201_CREATED)
def record_supplier_invoice(
    payload: SupplierInvoiceCreate,
    current_user: User = Depends(require_ap_access),
    db: Session = Depends(get_db),
):
    """
    Record an inbound supplier invoice against a Purchase Order (3-way matching).
    Calculates PO-to-Invoice variance and initializes balance_amount = total_amount.
    """
    po = db.get(PurchaseOrder, payload.purchase_order_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    # Check for duplicate invoice number from same supplier
    dup = db.execute(
        select(SupplierInvoice).where(
            SupplierInvoice.supplier_id == po.supplier_id,
            SupplierInvoice.invoice_number == payload.invoice_number.strip(),
        )
    ).scalar_one_or_none()

    if dup:
        raise HTTPException(
            status_code=400,
            detail=f"Invoice number '{payload.invoice_number}' has already been recorded for this supplier",
        )

    inv_date = payload.invoice_date or date.today()
    due_date = payload.due_date or (inv_date + timedelta(days=30))
    if due_date < inv_date:
        raise HTTPException(status_code=400, detail="due_date cannot be earlier than invoice_date")

    invoice = SupplierInvoice(
        invoice_number=payload.invoice_number.strip(),
        purchase_order_id=po.id,
        supplier_id=po.supplier_id,
        invoice_date=inv_date,
        due_date=due_date,
        subtotal=payload.subtotal,
        tax_amount=payload.tax_amount,
        total_amount=payload.total_amount,
        paid_amount=Decimal("0.00"),
        balance_amount=payload.total_amount,
        payment_status="PENDING",
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="SUPPLIER_INVOICE_CREATE",
        entity_name="SUPPLIER_INVOICE",
        entity_id=invoice.id,
        details={
            "invoice_number": invoice.invoice_number,
            "po_number": po.po_number,
            "total_amount": float(invoice.total_amount),
        },
    )
    db.commit()

    supplier = db.get(Supplier, po.supplier_id)
    variance = invoice.total_amount - po.total_amount

    return APIResponse(
        message=f"Supplier invoice '{invoice.invoice_number}' recorded successfully",
        data=SupplierInvoiceResponse(
            id=invoice.id,
            invoice_number=invoice.invoice_number,
            purchase_order_id=invoice.purchase_order_id,
            po_number=po.po_number,
            po_total=po.total_amount,
            supplier_id=invoice.supplier_id,
            supplier_name=supplier.company_name if supplier else None,
            supplier_gstin=supplier.gst_number if supplier else None,
            invoice_date=invoice.invoice_date,
            due_date=invoice.due_date,
            subtotal=invoice.subtotal,
            tax_amount=invoice.tax_amount,
            total_amount=invoice.total_amount,
            paid_amount=invoice.paid_amount,
            balance_amount=invoice.balance_amount,
            payment_status=invoice.payment_status,
            variance_amount=variance,
            created_at=invoice.created_at,
            updated_at=invoice.updated_at,
        ),
    )


@router.patch("/supplier-invoices/{id}/status", response_model=APIResponse[SupplierInvoiceResponse])
def update_supplier_invoice_status(
    id: int,
    payload: SupplierInvoiceStatusUpdate,
    current_user: User = Depends(require_finance_manager),
    db: Session = Depends(get_db),
):
    inv = db.get(SupplierInvoice, id)
    if not inv:
        raise HTTPException(status_code=404, detail="Supplier invoice not found")

    target = payload.payment_status.strip().upper()
    if target not in VALID_SUPPLIER_INVOICE_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid payment status '{target}'")

    inv.payment_status = target
    db.commit()
    db.refresh(inv)

    po = db.get(PurchaseOrder, inv.purchase_order_id)
    supplier = db.get(Supplier, inv.supplier_id)
    variance = (inv.total_amount - po.total_amount) if po else Decimal("0.00")

    return APIResponse(
        message=f"Supplier invoice status updated to '{target}'",
        data=SupplierInvoiceResponse(
            id=inv.id,
            invoice_number=inv.invoice_number,
            purchase_order_id=inv.purchase_order_id,
            po_number=po.po_number if po else None,
            po_total=po.total_amount if po else None,
            supplier_id=inv.supplier_id,
            supplier_name=supplier.company_name if supplier else None,
            supplier_gstin=supplier.gst_number if supplier else None,
            invoice_date=inv.invoice_date,
            due_date=inv.due_date,
            subtotal=inv.subtotal,
            tax_amount=inv.tax_amount,
            total_amount=inv.total_amount,
            paid_amount=inv.paid_amount,
            balance_amount=inv.balance_amount,
            payment_status=inv.payment_status,
            variance_amount=variance,
            created_at=inv.created_at,
            updated_at=inv.updated_at,
        ),
    )


# ==========================================
# 2. SUPPLIER PAYMENTS & ALLOCATIONS
# ==========================================

@router.get("/supplier-payments", response_model=APIResponse[dict])
def list_supplier_payments(
    supplier_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_ap_access),
    db: Session = Depends(get_db),
):
    query = select(SupplierPayment).options(
        selectinload(SupplierPayment.supplier),
        selectinload(SupplierPayment.creator),
    )

    if supplier_id:
        query = query.where(SupplierPayment.supplier_id == supplier_id)
    if status_filter:
        query = query.where(SupplierPayment.status == status_filter.strip().upper())

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0

    payments = (
        db.execute(
            query.order_by(SupplierPayment.payment_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    items = [
        SupplierPaymentResponse(
            id=p.id,
            payment_reference=p.payment_reference,
            supplier_id=p.supplier_id,
            supplier_name=p.supplier.company_name if p.supplier else None,
            payment_date=p.payment_date,
            payment_mode=p.payment_mode,
            amount=p.amount,
            unallocated_amount=p.unallocated_amount,
            status=p.status,
            notes=p.notes,
            created_by=p.created_by,
            creator_name=p.creator.full_name if p.creator else None,
            created_at=p.created_at,
        )
        for p in payments
    ]

    return APIResponse(
        message="Supplier payments retrieved",
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        },
    )


@router.post("/supplier-payments", response_model=APIResponse[SupplierPaymentResponse], status_code=status.HTTP_201_CREATED)
def record_supplier_payment(
    payload: SupplierPaymentCreate,
    current_user: User = Depends(require_finance_manager),
    db: Session = Depends(get_db),
):
    supplier = db.get(Supplier, payload.supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    pay_ref = payload.payment_reference or _generate_supplier_payment_ref(db)

    payment = SupplierPayment(
        payment_reference=pay_ref,
        supplier_id=supplier.id,
        payment_date=payload.payment_date,
        payment_mode=payload.payment_mode,
        amount=payload.amount,
        unallocated_amount=payload.amount,
        status="COMPLETED",
        notes=payload.notes,
        created_by=current_user.id,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="SUPPLIER_PAYMENT_CREATE",
        entity_name="SUPPLIER_PAYMENT",
        entity_id=payment.id,
        details={"payment_reference": payment.payment_reference, "amount": float(payment.amount)},
    )
    db.commit()

    return APIResponse(
        message=f"Supplier payment '{payment.payment_reference}' of ₹{payment.amount} recorded",
        data=SupplierPaymentResponse(
            id=payment.id,
            payment_reference=payment.payment_reference,
            supplier_id=payment.supplier_id,
            supplier_name=supplier.company_name,
            payment_date=payment.payment_date,
            payment_mode=payment.payment_mode,
            amount=payment.amount,
            unallocated_amount=payment.unallocated_amount,
            status=payment.status,
            notes=payment.notes,
            created_by=payment.created_by,
            creator_name=current_user.full_name,
            created_at=payment.created_at,
        ),
    )


@router.post("/supplier-invoices/{id}/allocations", response_model=APIResponse[SupplierInvoiceDetailResponse], status_code=status.HTTP_201_CREATED)
def allocate_supplier_payment_to_invoice(
    id: int,
    payload: SupplierPaymentAllocationCreate,
    current_user: User = Depends(require_finance_manager),
    db: Session = Depends(get_db),
):
    """
    Atomically allocate an existing supplier payment against an outstanding supplier invoice balance.
    """
    inv = db.execute(select(SupplierInvoice).where(SupplierInvoice.id == id).with_for_update()).scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Supplier invoice not found")

    payment = db.execute(select(SupplierPayment).where(SupplierPayment.id == payload.supplier_payment_id).with_for_update()).scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Supplier payment not found")

    if payment.supplier_id != inv.supplier_id:
        raise HTTPException(status_code=400, detail="Payment supplier and invoice supplier must match")

    alloc_amt = payload.allocated_amount
    if alloc_amt <= 0:
        raise HTTPException(status_code=400, detail="Allocated amount must be positive")

    if payment.unallocated_amount < alloc_amt:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient unallocated payment funds. Unallocated: ₹{payment.unallocated_amount}, Requested: ₹{alloc_amt}",
        )

    if inv.balance_amount < alloc_amt:
        raise HTTPException(
            status_code=400,
            detail=f"Allocation amount ₹{alloc_amt} exceeds invoice balance amount ₹{inv.balance_amount}",
        )

    # Apply atomic financial updates
    payment.unallocated_amount -= alloc_amt
    inv.paid_amount += alloc_amt
    inv.balance_amount -= alloc_amt

    if inv.balance_amount == Decimal("0.00"):
        inv.payment_status = "PAID"
    else:
        inv.payment_status = "PARTIALLY_PAID"

    allocation = SupplierPaymentAllocation(
        supplier_payment_id=payment.id,
        supplier_invoice_id=inv.id,
        allocated_amount=alloc_amt,
        allocated_at=datetime.now(timezone.utc),
    )
    db.add(allocation)
    db.commit()

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="SUPPLIER_PAYMENT_ALLOCATION",
        entity_name="SUPPLIER_INVOICE",
        entity_id=inv.id,
        details={
            "invoice_number": inv.invoice_number,
            "allocated_amount": float(alloc_amt),
            "remaining_balance": float(inv.balance_amount),
        },
    )
    db.commit()

    return get_supplier_invoice(inv.id, current_user, db)


@router.post("/supplier-invoices/{id}/payments", response_model=APIResponse[SupplierInvoiceDetailResponse], status_code=status.HTTP_201_CREATED)
def direct_supplier_invoice_payment(
    id: int,
    payload: DirectSupplierInvoicePaymentCreate,
    current_user: User = Depends(require_finance_manager),
    db: Session = Depends(get_db),
):
    """
    Direct payment to a supplier invoice: creates SupplierPayment and allocates atomically in a single transaction.
    """
    inv = db.execute(select(SupplierInvoice).where(SupplierInvoice.id == id).with_for_update()).scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Supplier invoice not found")

    pay_amt = payload.amount
    if pay_amt <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be positive")

    if pay_amt > inv.balance_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Payment amount ₹{pay_amt} exceeds invoice balance ₹{inv.balance_amount}",
        )

    pay_ref = payload.payment_reference or _generate_supplier_payment_ref(db)

    # 1. Create Supplier Payment
    payment = SupplierPayment(
        payment_reference=pay_ref,
        supplier_id=inv.supplier_id,
        payment_date=payload.payment_date,
        payment_mode=payload.payment_mode,
        amount=pay_amt,
        unallocated_amount=Decimal("0.00"),  # fully allocated
        status="COMPLETED",
        notes=payload.notes,
        created_by=current_user.id,
    )
    db.add(payment)
    db.flush()

    # 2. Update Invoice
    inv.paid_amount += pay_amt
    inv.balance_amount -= pay_amt
    if inv.balance_amount == Decimal("0.00"):
        inv.payment_status = "PAID"
    else:
        inv.payment_status = "PARTIALLY_PAID"

    # 3. Create Allocation
    alloc = SupplierPaymentAllocation(
        supplier_payment_id=payment.id,
        supplier_invoice_id=inv.id,
        allocated_amount=pay_amt,
        allocated_at=datetime.now(timezone.utc),
    )
    db.add(alloc)
    db.commit()

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="DIRECT_SUPPLIER_PAYMENT",
        entity_name="SUPPLIER_INVOICE",
        entity_id=inv.id,
        details={"payment_reference": payment.payment_reference, "amount": float(pay_amt)},
    )
    db.commit()

    return get_supplier_invoice(inv.id, current_user, db)


# ==========================================
# 3. PROJECT COSTS & PROFITABILITY
# ==========================================

@router.get("/projects/{project_id}/costs", response_model=APIResponse[List[ProjectCostResponse]])
def get_project_costs(
    project_id: int,
    current_user: User = Depends(require_ap_access),
    db: Session = Depends(get_db),
):
    costs = db.execute(
        select(ProjectCost)
        .options(selectinload(ProjectCost.recorder))
        .where(ProjectCost.project_id == project_id)
        .order_by(ProjectCost.created_at.desc())
    ).scalars().all()

    items = [
        ProjectCostResponse(
            id=c.id,
            project_id=c.project_id,
            cost_category=c.cost_category,
            cost_amount=c.cost_amount,
            source_reference_type=c.source_reference_type,
            source_reference_id=c.source_reference_id,
            recorded_by=c.recorded_by,
            recorder_name=c.recorder.full_name if c.recorder else None,
            created_at=c.created_at,
        )
        for c in costs
    ]
    return APIResponse(message="Project costs retrieved", data=items)


@router.post("/projects/{project_id}/costs", response_model=APIResponse[ProjectCostResponse], status_code=status.HTTP_201_CREATED)
def record_project_cost(
    project_id: int,
    payload: ProjectCostCreate,
    current_user: User = Depends(require_finance_manager),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cat = payload.cost_category.strip().upper()
    if cat not in VALID_COST_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid cost category '{cat}'")

    cost = ProjectCost(
        project_id=project.id,
        cost_category=cat,
        cost_amount=payload.cost_amount,
        source_reference_type=payload.source_reference_type,
        source_reference_id=payload.source_reference_id,
        recorded_by=current_user.id,
    )
    db.add(cost)
    db.commit()
    db.refresh(cost)

    return APIResponse(
        message=f"Direct project cost of ₹{cost.cost_amount} for {cost.cost_category} recorded",
        data=ProjectCostResponse(
            id=cost.id,
            project_id=cost.project_id,
            cost_category=cost.cost_category,
            cost_amount=cost.cost_amount,
            source_reference_type=cost.source_reference_type,
            source_reference_id=cost.source_reference_id,
            recorded_by=cost.recorded_by,
            recorder_name=current_user.full_name,
            created_at=cost.created_at,
        ),
    )


@router.get("/projects/{project_id}/profitability", response_model=APIResponse[ProjectProfitabilityResponse])
def get_project_profitability(
    project_id: int,
    current_user: User = Depends(require_ap_access),
    db: Session = Depends(get_db),
):
    """
    Project Profitability Analysis:
    - Contract Revenue (Order net payable / total amount)
    - Invoiced & Collected Customer Payments
    - Procurement Material Cost (Project BOM lines unit_cost * planned/dispatched)
    - Labor & Installation Direct Costs
    - Total Incurred Costs
    - Gross Profit & Gross Margin %
    """
    project = (
        db.execute(
            select(Project)
            .options(
                selectinload(Project.order),
                selectinload(Project.customer),
                selectinload(Project.bom_items),
            )
            .where(Project.id == project_id)
        )
        .scalars()
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    contract_amt = project.order.total_amount if project.order else Decimal("0.00")

    # Invoiced total & customer collected
    invoiced_sum = db.execute(
        select(func.coalesce(func.sum(Invoice.total_amount), Decimal("0.00")))
        .where(Invoice.project_id == project.id, Invoice.payment_status != "CANCELLED")
    ).scalar() or Decimal("0.00")

    collected_sum = db.execute(
        select(func.coalesce(func.sum(Invoice.paid_amount), Decimal("0.00")))
        .where(Invoice.project_id == project.id, Invoice.payment_status != "CANCELLED")
    ).scalar() or Decimal("0.00")

    # Material cost from Project BOM items
    material_cost = Decimal("0.00")
    for b in (project.bom_items or []):
        qty = b.dispatched_quantity if b.dispatched_quantity > 0 else b.planned_quantity
        unit_c = b.unit_cost_snapshot or Decimal("0.00")
        material_cost += (qty * unit_c)

    # Direct project costs
    costs = db.execute(
        select(ProjectCost).where(ProjectCost.project_id == project.id)
    ).scalars().all()

    labor_cost = Decimal("0.00")
    other_costs = Decimal("0.00")
    for c in costs:
        if c.cost_category in {"LABOR", "CIVIL_WORK"}:
            labor_cost += c.cost_amount
        else:
            other_costs += c.cost_amount

    # Approved expenses
    exp_sum = db.execute(
        select(func.coalesce(func.sum(Expense.amount), Decimal("0.00")))
        .where(Expense.project_id == project.id, Expense.payment_status == "PAID")
    ).scalar() or Decimal("0.00")
    other_costs += exp_sum

    total_incurred = material_cost + labor_cost + other_costs
    gross_profit = contract_amt - total_incurred
    margin_pct = (gross_profit / contract_amt * Decimal("100.00")) if contract_amt > 0 else Decimal("0.00")

    return APIResponse(
        message=f"Profitability analysis for project '{project.project_code}' calculated",
        data=ProjectProfitabilityResponse(
            project_id=project.id,
            project_code=project.project_code,
            order_id=project.order_id,
            order_number=project.order.order_number if project.order else "",
            customer_name=project.customer.full_name if project.customer else "",
            contract_amount=contract_amt,
            total_invoiced=invoiced_sum,
            total_collected=collected_sum,
            material_cost=material_cost,
            labor_installation_cost=labor_cost,
            other_direct_costs=other_costs,
            total_incurred_cost=total_incurred,
            gross_profit=gross_profit,
            gross_margin_percentage=round(margin_pct, 2),
        ),
    )
