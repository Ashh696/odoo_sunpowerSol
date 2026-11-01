from typing import Optional, List
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
from app.models.crm import Customer, Quotation, Enquiry
from app.models.projects import Order, Project
from app.models.finance import Payment
from app.models.workflow import AuditLog, Notification
from app.dependencies.auth import get_current_user, require_permissions, get_user_permissions
from app.utils.roles import SystemRole
from app.schemas import APIResponse
from app.schemas.orders import (
    OrderCreateRequest,
    OrderStatusUpdateRequest,
    OrderPaymentRecordRequest,
    OrderCustomerSummary,
    OrderQuotationSummary,
    OrderProjectSummary,
    OrderPaymentSummary,
    OrderResponse,
    OrderListResponse,
    VALID_ORDER_STATUSES,
    VALID_PAYMENT_METHODS,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["Orders"])


# ==========================================
# AUDIT & NOTIFICATION HELPERS
# ==========================================

def _record_audit_log(
    db: Session,
    user_id: Optional[int],
    action: str,
    entity_id: int,
    details: Optional[dict] = None,
):
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_name="ORDER",
        entity_id=entity_id,
        details=details or {},
    )
    db.add(log)


def _send_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "SYSTEM",
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


def _build_order_response(order: Order, db: Session) -> OrderResponse:
    # 1. Customer summary
    cust_summary = None
    if order.customer:
        cust_summary = OrderCustomerSummary(
            id=order.customer.id,
            full_name=order.customer.full_name,
            phone=order.customer.phone,
            email=order.customer.email,
            city=order.customer.city,
            state=order.customer.state,
        )

    # 2. Quotation summary
    quo_summary = None
    if order.quotation:
        quo_summary = OrderQuotationSummary(
            id=order.quotation.id,
            quotation_number=order.quotation.quotation_number,
            system_type=order.quotation.system_type,
            capacity_kw=Decimal(str(order.quotation.capacity_kw)),
            gross_amount=Decimal(str(order.quotation.gross_amount)),
            net_payable_amount=Decimal(str(order.quotation.net_payable_amount)),
            status=order.quotation.status,
        )

    # 3. Project summary (if one exists)
    proj_summary = None
    if order.project:
        proj_summary = OrderProjectSummary(
            id=order.project.id,
            project_code=order.project.project_code,
            status=order.project.status,
            system_capacity_kw=Decimal(str(order.project.system_capacity_kw)),
            system_type=order.project.system_type,
            planned_start_date=order.project.planned_start_date,
            planned_completion_date=order.project.planned_completion_date,
        )

    # 4. Payments summary
    payments_data = db.execute(
        select(Payment).where(Payment.order_id == order.id).order_by(Payment.created_at.asc())
    ).scalars().all()

    pay_summaries = [
        OrderPaymentSummary(
            id=p.id,
            payment_number=p.payment_number,
            payment_date=p.payment_date,
            payment_method=p.payment_method,
            transaction_reference=p.transaction_reference,
            amount=Decimal(str(p.amount)),
            unallocated_amount=Decimal(str(p.unallocated_amount)),
            status=p.status,
            notes=p.notes,
            created_at=p.created_at,
        )
        for p in payments_data
    ]

    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        quotation_id=order.quotation_id,
        customer_id=order.customer_id,
        order_date=order.order_date,
        total_amount=Decimal(str(order.total_amount)),
        advance_paid=Decimal(str(order.advance_paid)),
        balance_amount=Decimal(str(order.balance_amount)),
        status=order.status,
        created_by=order.created_by,
        created_at=order.created_at,
        updated_at=order.updated_at,
        customer=cust_summary,
        quotation=quo_summary,
        project=proj_summary,
        payments=pay_summaries,
    )


# ==========================================
# ORDER ENDPOINTS
# ==========================================

@router.post("", response_model=APIResponse[OrderResponse], status_code=status.HTTP_201_CREATED)
def create_order_from_quotation(
    payload: OrderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("orders.create")),
):
    """
    Manual conversion of an ACCEPTED quotation into a confirmed/pending-advance customer Order.
    Requires 'orders.create' permission (held by SUPER_ADMIN).
    Row-level locking serializes concurrent conversion attempts.
    Enforces that only ACCEPTED quotations can be converted, and at most one order per quotation.
    """
    # 1. Row-level lock on the target Quotation
    quotation = db.execute(
        select(Quotation)
        .options(
            selectinload(Quotation.enquiry).selectinload(Enquiry.customer),
            selectinload(Quotation.items),
        )
        .where(Quotation.id == payload.quotation_id)
        .with_for_update()
    ).scalar_one_or_none()

    if not quotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quotation with ID {payload.quotation_id} not found.",
        )

    # 2. Strict status check: Only ACCEPTED quotations qualify
    if quotation.status != "ACCEPTED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot create order: Quotation '{quotation.quotation_number}' is in status '{quotation.status}'. Only ACCEPTED quotations can be converted into orders.",
        )

    # 3. Check if an order already exists for this quotation
    existing_order = db.execute(
        select(Order).where(Order.quotation_id == quotation.id)
    ).scalar_one_or_none()

    if existing_order:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An order ('{existing_order.order_number}') has already been created for quotation '{quotation.quotation_number}'. At most one order per quotation is permitted.",
        )

    # 4. Build collision-resistant order number
    order_num = f"ORD-{date.today().year}-{uuid.uuid4().hex[:6].upper()}"

    total_amt = Decimal(str(quotation.net_payable_amount))
    advance_amt = Decimal("0.00")
    bal_amt = total_amt

    customer_id = quotation.enquiry.customer_id if quotation.enquiry else None
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quotation is missing associated enquiry customer.",
        )

    order = Order(
        order_number=order_num,
        quotation_id=quotation.id,
        customer_id=customer_id,
        order_date=date.today(),
        total_amount=total_amt,
        advance_paid=advance_amt,
        balance_amount=bal_amt,
        status="PENDING_ADVANCE",
        created_by=current_user.id,
    )
    db.add(order)

    try:
        db.flush()  # Allocate order.id and trigger DB unique constraints
    except IntegrityError as exc:
        db.rollback()
        err_msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)
        if "quotation_id" in err_msg.lower() or "unique" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An order has already been created for quotation '{quotation.quotation_number}'. Duplicate order rejected.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error while creating order: {err_msg}",
        )

    # 5. Audit log
    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="ORDER_CREATED",
        entity_id=order.id,
        details={
            "order_number": order.order_number,
            "quotation_id": quotation.id,
            "quotation_number": quotation.quotation_number,
            "customer_id": customer_id,
            "total_amount": float(total_amt),
            "status": order.status,
            "notes": payload.notes,
        },
    )

    # 6. Notify sales creator
    if quotation.created_by:
        _send_notification(
            db=db,
            user_id=quotation.created_by,
            title="Order Generated",
            message=f"Order {order.order_number} has been generated from accepted quotation {quotation.quotation_number}.",
            notification_type="SYSTEM",
        )

    db.commit()

    # Re-fetch with relationships loaded
    loaded_order = db.execute(
        select(Order)
        .options(
            selectinload(Order.customer),
            selectinload(Order.quotation),
            selectinload(Order.project),
        )
        .where(Order.id == order.id)
    ).scalar_one()

    return APIResponse(
        success=True,
        message=f"Order '{loaded_order.order_number}' created successfully from quotation '{quotation.quotation_number}'.",
        data=_build_order_response(loaded_order, db),
    )


@router.get("", response_model=APIResponse[OrderListResponse])
def list_orders(
    search: Optional[str] = Query(None, description="Search by order number or customer name"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    quotation_id: Optional[int] = Query(None, description="Filter by quotation ID"),
    status: Optional[str] = Query(None, description="Filter by order status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("orders.read")),
):
    """
    List orders with search, customer, quotation, and status filters.
    Applies strict customer isolation: Customer accounts can only view their own orders.
    """
    stmt = (
        select(Order)
        .options(
            selectinload(Order.customer),
            selectinload(Order.quotation),
            selectinload(Order.project),
        )
    )

    # Customer isolation
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        customer = _get_customer_for_user(current_user, db)
        if not customer:
            return APIResponse(
                success=True,
                message="No orders found",
                data=OrderListResponse(items=[], total=0, page=page, limit=limit, pages=0),
            )
        stmt = stmt.where(Order.customer_id == customer.id)
    elif customer_id:
        stmt = stmt.where(Order.customer_id == customer_id)

    if quotation_id:
        stmt = stmt.where(Order.quotation_id == quotation_id)

    if status:
        clean_status = status.strip().upper()
        stmt = stmt.where(Order.status == clean_status)

    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.join(Order.customer).where(
            or_(
                Order.order_number.ilike(term),
                Customer.full_name.ilike(term),
                Customer.phone.ilike(term),
            )
        )

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar() or 0

    # Paginate
    offset = (page - 1) * limit
    orders = db.execute(
        stmt.order_by(Order.created_at.desc()).offset(offset).limit(limit)
    ).scalars().all()

    pages = (total + limit - 1) // limit if total > 0 else 0
    items = [_build_order_response(o, db) for o in orders]

    return APIResponse(
        success=True,
        message=f"Retrieved {len(items)} orders.",
        data=OrderListResponse(items=items, total=total, page=page, limit=limit, pages=pages),
    )


@router.get("/{id}", response_model=APIResponse[OrderResponse])
def get_order(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("orders.read")),
):
    """
    Retrieve full order details including customer, quotation, project, and payment history.
    Enforces customer ownership verification.
    """
    order = db.execute(
        select(Order)
        .options(
            selectinload(Order.customer),
            selectinload(Order.quotation),
            selectinload(Order.project),
        )
        .where(Order.id == id)
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {id} not found.",
        )

    # Customer isolation
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        customer = _get_customer_for_user(current_user, db)
        if not customer or order.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access orders associated with your own customer account.",
            )

    return APIResponse(
        success=True,
        message="Order retrieved successfully.",
        data=_build_order_response(order, db),
    )


@router.put("/{id}/status", response_model=APIResponse[OrderResponse])
def update_order_status(
    id: int,
    payload: OrderStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("orders.update")),
):
    """
    Update order execution status. Requires 'orders.update' permission (held by SUPER_ADMIN).
    Enforces valid status transitions and audits changes.
    """
    order = db.execute(
        select(Order)
        .options(
            selectinload(Order.customer),
            selectinload(Order.quotation),
            selectinload(Order.project),
        )
        .where(Order.id == id)
        .with_for_update()
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {id} not found.",
        )

    target_status = payload.status.strip().upper()
    if target_status not in VALID_ORDER_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid order status '{target_status}'. Permitted: {sorted(list(VALID_ORDER_STATUSES))}",
        )

    old_status = order.status
    if old_status == target_status:
        return APIResponse(
            success=True,
            message=f"Order is already in status '{target_status}'.",
            data=_build_order_response(order, db),
        )

    # Disallow reviving CANCELLED orders
    if old_status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot update status of a CANCELLED order.",
        )

    order.status = target_status

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="ORDER_STATUS_UPDATED",
        entity_id=order.id,
        details={
            "old_status": old_status,
            "new_status": target_status,
            "notes": payload.notes,
        },
    )

    db.commit()
    db.refresh(order)

    return APIResponse(
        success=True,
        message=f"Order status updated from '{old_status}' to '{target_status}'.",
        data=_build_order_response(order, db),
    )


@router.post("/{id}/payments", response_model=APIResponse[OrderResponse], status_code=status.HTTP_201_CREATED)
def record_order_payment(
    id: int,
    payload: OrderPaymentRecordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("payments.record")),
):
    """
    Record an advance or milestone customer payment against an existing Order.
    Requires 'payments.record' permission (held by SUPER_ADMIN, FINANCE_ACCOUNTS).
    Updates order.advance_paid and order.balance_amount atomically.
    Prevents overpayment and validates payment method.
    """
    order = db.execute(
        select(Order)
        .options(
            selectinload(Order.customer),
            selectinload(Order.quotation),
            selectinload(Order.project),
        )
        .where(Order.id == id)
        .with_for_update()
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {id} not found.",
        )

    if order.status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot record payment against a CANCELLED order.",
        )

    pay_method = payload.payment_method.strip().upper()
    if pay_method not in VALID_PAYMENT_METHODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payment method '{pay_method}'. Permitted: {sorted(list(VALID_PAYMENT_METHODS))}",
        )

    # Validate payment amount against balance
    if payload.amount <= Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be greater than 0.",
        )

    current_balance = Decimal(str(order.balance_amount))
    if payload.amount > current_balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment amount ({payload.amount}) exceeds outstanding order balance ({current_balance}). Overpayment is not permitted.",
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

    # Generate payment number
    pay_number = f"PAY-{date.today().year}-{uuid.uuid4().hex[:6].upper()}"

    payment = Payment(
        payment_number=pay_number,
        customer_id=order.customer_id,
        order_id=order.id,
        project_id=order.project.id if order.project else None,
        payment_date=date.today(),
        payment_method=pay_method,
        transaction_reference=payload.transaction_reference.strip() if payload.transaction_reference else None,
        amount=payload.amount,
        unallocated_amount=payload.amount,
        status="COMPLETED",
        notes=payload.notes,
        received_by=current_user.id,
    )
    db.add(payment)

    # Reconcile order financial balances
    order.advance_paid = Decimal(str(order.advance_paid)) + payload.amount
    order.balance_amount = Decimal(str(order.total_amount)) - order.advance_paid

    # If order was in PENDING_ADVANCE, transition to CONFIRMED
    if order.status == "PENDING_ADVANCE":
        order.status = "CONFIRMED"

    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        err_msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Database conflict during payment recording: {err_msg}",
        )

    # Audit log
    log = AuditLog(
        user_id=current_user.id,
        action="PAYMENT_RECORDED",
        entity_name="PAYMENT",
        entity_id=payment.id,
        details={
            "payment_number": payment.payment_number,
            "order_id": order.id,
            "amount": float(payload.amount),
            "payment_method": pay_method,
            "new_order_advance": float(order.advance_paid),
            "new_order_balance": float(order.balance_amount),
            "order_status": order.status,
        },
    )
    db.add(log)

    db.commit()
    db.refresh(order)

    return APIResponse(
        success=True,
        message=f"Payment '{payment.payment_number}' of INR {payload.amount} recorded successfully. Order balance updated.",
        data=_build_order_response(order, db),
    )
