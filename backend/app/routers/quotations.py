from typing import List, Optional, Dict, Any, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_, and_
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import math
import logging

from app.database import get_db
from app.models.crm import Quotation, QuotationItem, QuotationRevision, Product, Survey, Enquiry, Customer
from app.models.auth import User
from app.models.workflow import AuditLog, Notification
from app.schemas.quotations import (
    QuotationItemCreate,
    QuotationItemUpdate,
    QuotationItemResponse,
    QuotationRevisionResponse,
    QuotationRevisionRequest,
    QuotationCreate,
    QuotationUpdate,
    QuotationApprovalRequest,
    QuotationRejectionRequest,
    QuotationCustomerAcceptRequest,
    QuotationCustomerRejectRequest,
    CompanyProfileResponse,
    QuotationResponse,
    QuotationListResponse,
    VALID_QUOTATION_STATUSES,
    VALID_SYSTEM_TYPES,
)
from app.config import settings
from app.schemas import APIResponse
from app.dependencies.auth import get_current_user, get_user_permissions
from app.utils.roles import SystemRole

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quotations", tags=["Quotation Engine"])

TWOPLACES = Decimal("0.01")


# ==========================================
# INTERNAL ARITHMETIC & CALCULATION HELPERS
# ==========================================

def quantize_amount(val: Any) -> Decimal:
    """Consistently quantize amounts to 2 decimal places using standard ROUND_HALF_UP."""
    if val is None:
        return Decimal("0.00")
    if isinstance(val, (int, float, str)):
        return Decimal(str(val)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    if isinstance(val, Decimal):
        return val.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    return Decimal("0.00")


def calculate_line_item(
    quantity: Decimal,
    unit_price: Decimal,
    discount_amount: Decimal,
    tax_rate_percent: Decimal,
) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
    """
    Computes:
    1. base_amount = quantity * unit_price
    2. discounted_base = base_amount - discount_amount
    3. tax = discounted_base * (tax_rate_percent / 100)
    4. line_total = discounted_base + tax
    Returns (base_amount, discounted_base, tax, line_total).
    """
    qty = quantize_amount(quantity)
    price = quantize_amount(unit_price)
    discount = quantize_amount(discount_amount)
    tax_rate = quantize_amount(tax_rate_percent)

    if qty <= Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Line item quantity must be strictly greater than zero.",
        )
    if price < Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Line item unit price cannot be negative.",
        )
    if discount < Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Line item discount cannot be negative.",
        )
    if tax_rate < Decimal("0.00") or tax_rate > Decimal("100.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tax rate percent must be between 0.00% and 100.00%.",
        )

    base_amount = quantize_amount(qty * price)
    if discount > base_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Line item discount ({discount}) cannot exceed the line base amount ({base_amount}).",
        )

    discounted_base = quantize_amount(base_amount - discount)
    tax = quantize_amount(discounted_base * (tax_rate / Decimal("100.00")))
    line_total = quantize_amount(discounted_base + tax)

    return base_amount, discounted_base, tax, line_total


def compute_standard_subsidy_policy(customer_type: Optional[str], capacity_kw: Decimal) -> Decimal:
    """
    Isolated subsidy calculation policy.
    PM Surya Ghar standard residential rooftop benchmark:
    - Commercial or Industrial: 0.00
    - Residential <= 2 kW: 30,000 / kW (up to 60,000)
    - Residential 2 kW to 3 kW: 60,000 + 18,000 / kW for additional capacity (up to 78,000)
    - Residential > 3 kW: Capped at 78,000
    """
    if not customer_type or customer_type.upper() != "RESIDENTIAL":
        return Decimal("0.00")

    cap = Decimal(str(capacity_kw))
    if cap <= Decimal("0.00"):
        return Decimal("0.00")

    if cap <= Decimal("2.00"):
        sub = cap * Decimal("30000.00")
    elif cap <= Decimal("3.00"):
        sub = Decimal("60000.00") + (cap - Decimal("2.00")) * Decimal("18000.00")
    else:
        sub = Decimal("78000.00")

    return quantize_amount(min(sub, Decimal("78000.00")))


# ==========================================
# STATE MACHINE VALIDATION
# ==========================================

VALID_TRANSITIONS = {
    "DRAFT": {"PENDING_APPROVAL", "DRAFT"},
    "PENDING_APPROVAL": {"APPROVED", "REJECTED"},
    "APPROVED": {"SENT", "DRAFT"},  # DRAFT via revision
    "SENT": {"ACCEPTED", "REJECTED", "DRAFT"},  # DRAFT via revision
    "REJECTED": {"DRAFT"},  # DRAFT via revision
    "ACCEPTED": set(),  # Terminal state: completely immutable
}


def validate_status_transition(current_status: str, target_status: str):
    """Enforces central state machine rules."""
    if current_status == "ACCEPTED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Quotation has been ACCEPTED by customer and is completely immutable. No changes or transitions allowed.",
        )

    allowed = VALID_TRANSITIONS.get(current_status, set())
    if target_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid quotation status transition from {current_status} to {target_status}.",
        )


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
        entity_name="QUOTATION",
        entity_id=entity_id,
        details=details or {},
    )
    db.add(log)


def _send_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "APPROVAL",
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


# ==========================================
# AUTHORIZATION & CUSTOMER LINKING HELPERS
# ==========================================

def _get_customer_for_user(user: User, db: Session) -> Optional[Customer]:
    return db.execute(select(Customer).where(Customer.user_id == user.id)).scalar_one_or_none()


def require_quotation_read_access(current_user: User = Depends(get_current_user)) -> User:
    """
    SUPER_ADMIN has universal access.
    CUSTOMER, DIRECTOR, SALES, TECHNICAL_MANAGER have 'quotations.read'.
    WAREHOUSE_PROCUREMENT, FIELD_TECHNICIAN, and FINANCE_ACCOUNTS are blocked.
    """
    if current_user.role and current_user.role.slug == SystemRole.SUPER_ADMIN:
        return current_user

    if current_user.role and current_user.role.slug in (
        SystemRole.WAREHOUSE_PROCUREMENT,
        SystemRole.FIELD_TECHNICIAN,
        SystemRole.FINANCE_ACCOUNTS,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role privileges to access Quotation pricing.",
        )

    user_perms = get_user_permissions(current_user)
    if "quotations.read" in user_perms:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Missing required permission: quotations.read",
    )


def require_quotation_create_access(current_user: User = Depends(get_current_user)) -> User:
    """SUPER_ADMIN and SALES have create access."""
    if current_user.role and current_user.role.slug == SystemRole.SUPER_ADMIN:
        return current_user

    user_perms = get_user_permissions(current_user)
    if "quotations.create" in user_perms:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions to create quotations.",
    )


def require_quotation_update_access(current_user: User = Depends(get_current_user)) -> User:
    """SUPER_ADMIN and SALES have update/revision access."""
    if current_user.role and current_user.role.slug == SystemRole.SUPER_ADMIN:
        return current_user

    user_perms = get_user_permissions(current_user)
    if "quotations.update" in user_perms:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions to modify quotations.",
    )


def require_quotation_approve_access(current_user: User = Depends(get_current_user)) -> User:
    """
    SUPER_ADMIN, DIRECTOR, and TECHNICAL_MANAGER have approve access.
    SALES is strictly blocked from approving quotations.
    """
    if current_user.role and current_user.role.slug == SystemRole.SUPER_ADMIN:
        return current_user

    if current_user.role and current_user.role.slug == SystemRole.SALES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sales personnel cannot approve quotations.",
        )

    user_perms = get_user_permissions(current_user)
    if "quotations.approve" in user_perms:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Missing required permission: quotations.approve",
    )


# ==========================================
# CONCURRENCY-SAFE NUMBER GENERATOR
# ==========================================

def _generate_quotation_number_candidate(db: Session, q_date: date) -> str:
    """Generates candidate QUO-YYYYMM-XXXX sequence."""
    year_month = q_date.strftime("%Y%m")
    prefix = f"QUO-{year_month}-"

    max_num = db.execute(
        select(Quotation.quotation_number)
        .where(Quotation.quotation_number.like(f"{prefix}%"))
        .order_by(Quotation.quotation_number.desc())
        .limit(1)
    ).scalar_one_or_none()

    seq = 1
    if max_num:
        try:
            parts = max_num.split("-")
            if len(parts) == 3:
                seq = int(parts[2]) + 1
        except (ValueError, IndexError):
            seq = 1

    return f"{prefix}{seq:04d}"


# ==========================================
# RESPONSE BUILDER
# ==========================================

def _build_quotation_response(q: Quotation) -> QuotationResponse:
    creator_name = q.creator.full_name if q.creator else None
    enquiry_number = q.enquiry.enquiry_number if q.enquiry else None
    customer_id = q.enquiry.customer_id if q.enquiry else None
    customer_name = q.enquiry.customer.full_name if (q.enquiry and q.enquiry.customer) else None
    customer_type = q.enquiry.customer.customer_type if (q.enquiry and q.enquiry.customer) else None
    customer_phone = q.enquiry.customer.phone if (q.enquiry and q.enquiry.customer) else None
    customer_email = q.enquiry.customer.email if (q.enquiry and q.enquiry.customer) else None
    customer_address = q.enquiry.customer.address if (q.enquiry and q.enquiry.customer) else None
    customer_city = q.enquiry.customer.city if (q.enquiry and q.enquiry.customer) else None
    customer_state = q.enquiry.customer.state if (q.enquiry and q.enquiry.customer) else None
    customer_pincode = q.enquiry.customer.pincode if (q.enquiry and q.enquiry.customer) else None
    survey_number = q.survey.survey_number if q.survey else None

    # Optional Company Profile
    company_fields = {
        "legal_name": (getattr(settings, "COMPANY_LEGAL_NAME", None) or "").strip() or None,
        "gstin": (getattr(settings, "COMPANY_GSTIN", None) or "").strip() or None,
        "address": (getattr(settings, "COMPANY_ADDRESS", None) or "").strip() or None,
        "phone": (getattr(settings, "COMPANY_PHONE", None) or "").strip() or None,
        "email": (getattr(settings, "COMPANY_EMAIL", None) or "").strip() or None,
        "bank_name": (getattr(settings, "COMPANY_BANK_NAME", None) or "").strip() or None,
        "bank_account_name": (getattr(settings, "COMPANY_BANK_ACCOUNT_NAME", None) or "").strip() or None,
        "bank_account_no": (getattr(settings, "COMPANY_BANK_ACCOUNT_NO", None) or "").strip() or None,
        "bank_ifsc": (getattr(settings, "COMPANY_BANK_IFSC", None) or "").strip() or None,
        "bank_branch": (getattr(settings, "COMPANY_BANK_BRANCH", None) or "").strip() or None,
    }
    has_company_info = any(v is not None for v in company_fields.values())
    company_profile = CompanyProfileResponse(**company_fields) if has_company_info else None

    item_responses = [
        QuotationItemResponse(
            id=item.id,
            quotation_id=item.quotation_id,
            product_id=item.product_id,
            product_code=item.product.product_code if item.product else None,
            product_name=item.product.name if item.product else None,
            brand=item.product.brand if item.product else None,
            model_number=item.product.model_number if item.product else None,
            item_description=item.item_description,
            quantity=float(item.quantity),
            unit_price=float(item.unit_price),
            discount_amount=float(item.discount_amount),
            tax_rate_percent=float(item.tax_rate_percent),
            total_amount=float(item.total_amount),
            created_at=item.created_at,
        )
        for item in (q.items or [])
    ]

    revision_responses = [
        QuotationRevisionResponse(
            id=rev.id,
            quotation_id=rev.quotation_id,
            revision_number=rev.revision_number,
            snapshot_data=rev.snapshot_data or {},
            reason_for_revision=rev.reason_for_revision,
            revised_by=rev.revised_by,
            revised_by_name=rev.reviser.full_name if rev.reviser else None,
            created_at=rev.created_at,
        )
        for rev in (q.revisions or [])
    ]

    return QuotationResponse(
        id=q.id,
        quotation_number=q.quotation_number,
        version=q.version,
        enquiry_id=q.enquiry_id,
        enquiry_number=enquiry_number,
        customer_id=customer_id,
        customer_name=customer_name,
        customer_type=customer_type,
        customer_phone=customer_phone,
        customer_email=customer_email,
        customer_address=customer_address,
        customer_city=customer_city,
        customer_state=customer_state,
        customer_pincode=customer_pincode,
        survey_id=q.survey_id,
        survey_number=survey_number,
        system_type=q.system_type,
        capacity_kw=float(q.capacity_kw),
        total_product_cost=float(q.total_product_cost),
        installation_cost=float(q.installation_cost),
        tax_amount=float(q.tax_amount),
        gross_amount=float(q.gross_amount),
        subsidy_estimate=float(q.subsidy_estimate),
        net_payable_amount=float(q.net_payable_amount),
        status=q.status,
        quotation_date=q.quotation_date,
        valid_until=q.valid_until,
        terms_and_conditions=q.terms_and_conditions,
        created_by=q.created_by,
        creator_name=creator_name,
        company_profile=company_profile,
        items=item_responses,
        revisions=revision_responses,
        created_at=q.created_at,
        updated_at=q.updated_at,
    )


# ==========================================
# ENDPOINTS
# ==========================================

@router.post("", response_model=APIResponse[QuotationResponse], status_code=status.HTTP_201_CREATED)
def create_quotation(
    payload: QuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_quotation_create_access),
):
    """
    Create a new Quotation in DRAFT status, version 1.
    Snapshots product prices and tax rates from active catalog products.
    Enforces APPROVED survey checks and decimal calculations.
    """
    # 1. Verify Enquiry
    enquiry = db.execute(
        select(Enquiry)
        .options(selectinload(Enquiry.customer))
        .where(Enquiry.id == payload.enquiry_id)
    ).scalar_one_or_none()

    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enquiry with ID {payload.enquiry_id} not found.",
        )

    # 2. Survey Validation
    survey = None
    if payload.survey_id is not None:
        survey = db.execute(select(Survey).where(Survey.id == payload.survey_id)).scalar_one_or_none()
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Survey with ID {payload.survey_id} not found.",
            )
        if survey.enquiry_id != enquiry.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Survey ID {payload.survey_id} belongs to Enquiry ID {survey.enquiry_id}, not Enquiry ID {enquiry.id}.",
            )
        if survey.status != "APPROVED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Survey ID {payload.survey_id} is in status '{survey.status}'. Only APPROVED surveys can be used for quotations.",
            )
    else:
        # Check if enquiry has completed surveys requiring selection
        approved_surveys = db.execute(
            select(Survey).where(Survey.enquiry_id == enquiry.id, Survey.status == "APPROVED")
        ).scalars().all()
        if approved_surveys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Enquiry has approved survey(s). You must explicitly provide an approved survey_id.",
            )

    # 3. System Type and Capacity Consistency
    system_type = payload.system_type or enquiry.system_type or "ON_GRID"
    capacity_kw = payload.capacity_kw or enquiry.proposed_capacity_kw

    if not capacity_kw or capacity_kw <= Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quotation capacity_kw must be strictly positive.",
        )

    # 4. Dates
    quotation_date = date.today()
    if payload.valid_until is not None:
        if payload.valid_until < quotation_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"valid_until ({payload.valid_until}) must be on or after quotation_date ({quotation_date}).",
            )
        valid_until = payload.valid_until
    else:
        valid_until = quotation_date + timedelta(days=30)

    # 5. Product & Line Items Validation
    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quotation must contain at least one line item.",
        )

    quotation_items = []
    total_discounted_base = Decimal("0.00")
    total_tax_amount = Decimal("0.00")

    for item_in in payload.items:
        product = db.execute(select(Product).where(Product.id == item_in.product_id)).scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {item_in.product_id} not found.",
            )
        if not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.name}' ({product.product_code}) is inactive and cannot be added to a quotation.",
            )

        unit_price = item_in.unit_price if item_in.unit_price is not None else product.base_price
        tax_rate = item_in.tax_rate_percent if item_in.tax_rate_percent is not None else product.tax_rate_percent
        desc = item_in.item_description or product.name

        base_amt, disc_base, tax, line_total = calculate_line_item(
            quantity=item_in.quantity,
            unit_price=unit_price,
            discount_amount=item_in.discount_amount,
            tax_rate_percent=tax_rate,
        )

        q_item = QuotationItem(
            product_id=product.id,
            item_description=desc,
            quantity=quantize_amount(item_in.quantity),
            unit_price=quantize_amount(unit_price),
            discount_amount=quantize_amount(item_in.discount_amount),
            tax_rate_percent=quantize_amount(tax_rate),
            total_amount=quantize_amount(line_total),
        )
        quotation_items.append(q_item)

        total_discounted_base += disc_base
        total_tax_amount += tax

    # 6. Installation Cost & Gross Amount
    installation_cost = quantize_amount(payload.installation_cost)
    total_product_cost = quantize_amount(total_discounted_base)
    tax_amount = quantize_amount(total_tax_amount)
    gross_amount = quantize_amount(total_product_cost + installation_cost + tax_amount)

    # 7. Subsidy Policy Calculation & Override Workflow
    customer_type = enquiry.customer.customer_type if enquiry.customer else "RESIDENTIAL"
    standard_subsidy = compute_standard_subsidy_policy(customer_type, capacity_kw)

    subsidy_override_occurred = False
    if payload.subsidy_estimate is not None:
        subsidy_estimate = quantize_amount(payload.subsidy_estimate)
        if subsidy_estimate < Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subsidy estimate cannot be negative.",
            )
        if subsidy_estimate > gross_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subsidy estimate ({subsidy_estimate}) cannot exceed gross amount ({gross_amount}).",
            )
        if subsidy_estimate != standard_subsidy:
            if not payload.subsidy_override_reason or len(payload.subsidy_override_reason.strip()) < 3:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Explicit subsidy_override_reason (at least 3 characters) is required when overriding the standard subsidy policy estimate.",
                )
            subsidy_override_occurred = True
    else:
        subsidy_estimate = min(standard_subsidy, gross_amount)

    net_payable_amount = quantize_amount(max(Decimal("0.00"), gross_amount - subsidy_estimate))

    # 8. Concurrency-Safe Quotation Insertion with Retry Loop
    quotation = Quotation(
        enquiry_id=enquiry.id,
        survey_id=payload.survey_id,
        version=1,
        system_type=system_type,
        capacity_kw=quantize_amount(capacity_kw),
        total_product_cost=total_product_cost,
        installation_cost=installation_cost,
        tax_amount=tax_amount,
        gross_amount=gross_amount,
        subsidy_estimate=subsidy_estimate,
        net_payable_amount=net_payable_amount,
        status="DRAFT",
        quotation_date=quotation_date,
        valid_until=valid_until,
        created_by=current_user.id,
        terms_and_conditions=payload.terms_and_conditions,
    )

    for item in quotation_items:
        quotation.items.append(item)

    saved = False
    for attempt in range(5):
        try:
            cand_number = _generate_quotation_number_candidate(db, quotation_date)
            quotation.quotation_number = cand_number
            db.add(quotation)
            db.flush()
            saved = True
            break
        except IntegrityError as exc:
            db.rollback()
            # If conflict on quotation_number uniqueness, retry
            if "quotation_number" in str(exc).lower() or "unique" in str(exc).lower():
                if attempt == 4:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Failed to assign unique quotation number after concurrent attempts. Please retry.",
                    )
                continue
            raise

    if not saved:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error generating quotation.",
        )

    # 9. Audit Logging
    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="QUOTATION_CREATED",
        entity_id=quotation.id,
        details={
            "quotation_number": quotation.quotation_number,
            "version": quotation.version,
            "gross_amount": float(quotation.gross_amount),
            "net_payable_amount": float(quotation.net_payable_amount),
            "enquiry_id": quotation.enquiry_id,
            "items_count": len(quotation.items),
        },
    )

    if subsidy_override_occurred:
        _record_audit_log(
            db=db,
            user_id=current_user.id,
            action="SUBSIDY_OVERRIDDEN",
            entity_id=quotation.id,
            details={
                "previous_amount": float(standard_subsidy),
                "new_amount": float(subsidy_estimate),
                "reason": payload.subsidy_override_reason.strip(),
                "quotation_number": quotation.quotation_number,
            },
        )

    db.commit()

    # Re-fetch with all relationships loaded
    full_q = db.execute(
        select(Quotation)
        .options(
            selectinload(Quotation.creator),
            selectinload(Quotation.enquiry).selectinload(Enquiry.customer),
            selectinload(Quotation.survey),
            selectinload(Quotation.items).selectinload(QuotationItem.product),
            selectinload(Quotation.revisions).selectinload(QuotationRevision.reviser),
        )
        .where(Quotation.id == quotation.id)
    ).scalar_one()

    return APIResponse(
        success=True,
        message=f"Quotation {full_q.quotation_number} created successfully in DRAFT status.",
        data=_build_quotation_response(full_q),
    )


@router.get("", response_model=APIResponse[QuotationListResponse])
def list_quotations(
    search: Optional[str] = Query(None, description="Search by quotation number or customer name"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by quotation status"),
    enquiry_id: Optional[int] = Query(None, description="Filter by enquiry ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_quotation_read_access),
):
    """
    List quotations with pagination, status filtering, and search.
    If current user is CUSTOMER, only quotations belonging to their account are returned.
    """
    stmt = (
        select(Quotation)
        .join(Quotation.enquiry)
        .join(Enquiry.customer)
        .options(
            selectinload(Quotation.creator),
            selectinload(Quotation.enquiry).selectinload(Enquiry.customer),
            selectinload(Quotation.survey),
            selectinload(Quotation.items).selectinload(QuotationItem.product),
            selectinload(Quotation.revisions).selectinload(QuotationRevision.reviser),
        )
    )

    # Customer scope isolation
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        customer = _get_customer_for_user(current_user, db)
        if not customer:
            return APIResponse(
                success=True,
                message="No customer account associated with current user.",
                data=QuotationListResponse(items=[], total=0, page=page, limit=limit, pages=0),
            )
        stmt = stmt.where(Enquiry.customer_id == customer.id)

    # Filters
    if status_filter:
        s_upper = status_filter.strip().upper()
        stmt = stmt.where(Quotation.status == s_upper)

    if enquiry_id is not None:
        stmt = stmt.where(Quotation.enquiry_id == enquiry_id)

    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Quotation.quotation_number.ilike(term),
                Customer.full_name.ilike(term),
                Enquiry.enquiry_number.ilike(term),
            )
        )

    # Count total
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total_count = db.execute(count_stmt).scalar() or 0
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 0

    # Paginate
    stmt = stmt.order_by(Quotation.created_at.desc()).offset((page - 1) * limit).limit(limit)
    quotations = db.execute(stmt).scalars().all()

    return APIResponse(
        success=True,
        message="Quotations retrieved successfully.",
        data=QuotationListResponse(
            items=[_build_quotation_response(q) for q in quotations],
            total=total_count,
            page=page,
            limit=limit,
            pages=total_pages,
        ),
    )


@router.get("/{id}", response_model=APIResponse[QuotationResponse])
def get_quotation_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_quotation_read_access),
):
    """
    Get full quotation details including line items and revision history.
    Enforces customer ownership verification.
    """
    q = db.execute(
        select(Quotation)
        .options(
            selectinload(Quotation.creator),
            selectinload(Quotation.enquiry).selectinload(Enquiry.customer),
            selectinload(Quotation.survey),
            selectinload(Quotation.items).selectinload(QuotationItem.product),
            selectinload(Quotation.revisions).selectinload(QuotationRevision.reviser),
        )
        .where(Quotation.id == id)
    ).scalar_one_or_none()

    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quotation with ID {id} not found.",
        )

    # Customer isolation check
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        customer = _get_customer_for_user(current_user, db)
        if not customer or q.enquiry.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quotation with ID {id} not found.",
            )

    return APIResponse(
        success=True,
        message="Quotation details retrieved successfully.",
        data=_build_quotation_response(q),
    )


@router.put("/{id}", response_model=APIResponse[QuotationResponse])
def update_draft_quotation(
    id: int,
    payload: QuotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_quotation_update_access),
):
    """
    Update a DRAFT quotation. Only quotations in DRAFT status can be updated.
    Technical Managers and Directors cannot change sales pricing.
    """
    # Enforce role: Technical Manager and Director are read-only for pricing/draft modification
    if current_user.role and current_user.role.slug in (SystemRole.TECHNICAL_MANAGER, SystemRole.DIRECTOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Technical Managers and Directors cannot modify quotation sales pricing.",
        )

    q = db.execute(
        select(Quotation)
        .options(
            selectinload(Quotation.enquiry).selectinload(Enquiry.customer),
            selectinload(Quotation.items),
        )
        .where(Quotation.id == id)
        .with_for_update()
    ).scalar_one_or_none()

    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quotation with ID {id} not found.",
        )

    if q.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Only DRAFT quotations can be directly modified. Current status is '{q.status}'. Use the revision workflow if modification is required.",
        )

    # 1. Update basic fields if provided
    if payload.system_type is not None:
        q.system_type = payload.system_type
    if payload.capacity_kw is not None:
        if payload.capacity_kw <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="capacity_kw must be strictly greater than zero.",
            )
        q.capacity_kw = quantize_amount(payload.capacity_kw)
    if payload.terms_and_conditions is not None:
        q.terms_and_conditions = payload.terms_and_conditions
    if payload.valid_until is not None:
        if payload.valid_until < q.quotation_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"valid_until ({payload.valid_until}) must be on or after quotation_date ({q.quotation_date}).",
            )
        q.valid_until = payload.valid_until
    if payload.installation_cost is not None:
        q.installation_cost = quantize_amount(payload.installation_cost)

    # 2. Update line items if provided
    if payload.items is not None:
        if not payload.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quotation must contain at least one line item.",
            )

        # Clear existing items and replace
        q.items.clear()
        total_discounted_base = Decimal("0.00")
        total_tax_amount = Decimal("0.00")

        for item_in in payload.items:
            product = db.execute(select(Product).where(Product.id == item_in.product_id)).scalar_one_or_none()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {item_in.product_id} not found.",
                )
            if not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{product.name}' ({product.product_code}) is inactive and cannot be added.",
                )

            unit_price = item_in.unit_price if item_in.unit_price is not None else product.base_price
            tax_rate = item_in.tax_rate_percent if item_in.tax_rate_percent is not None else product.tax_rate_percent
            desc = item_in.item_description or product.name

            base_amt, disc_base, tax, line_total = calculate_line_item(
                quantity=item_in.quantity,
                unit_price=unit_price,
                discount_amount=item_in.discount_amount,
                tax_rate_percent=tax_rate,
            )

            new_item = QuotationItem(
                quotation_id=q.id,
                product_id=product.id,
                item_description=desc,
                quantity=quantize_amount(item_in.quantity),
                unit_price=quantize_amount(unit_price),
                discount_amount=quantize_amount(item_in.discount_amount),
                tax_rate_percent=quantize_amount(tax_rate),
                total_amount=quantize_amount(line_total),
            )
            q.items.append(new_item)
            total_discounted_base += disc_base
            total_tax_amount += tax

        q.total_product_cost = quantize_amount(total_discounted_base)
        q.tax_amount = quantize_amount(total_tax_amount)

    # 3. Recalculate totals
    q.gross_amount = quantize_amount(q.total_product_cost + q.installation_cost + q.tax_amount)

    # 4. Subsidy Policy & Override
    customer_type = q.enquiry.customer.customer_type if (q.enquiry and q.enquiry.customer) else "RESIDENTIAL"
    standard_subsidy = compute_standard_subsidy_policy(customer_type, q.capacity_kw)

    subsidy_override_occurred = False
    if payload.subsidy_estimate is not None:
        subsidy_estimate = quantize_amount(payload.subsidy_estimate)
        if subsidy_estimate < Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subsidy estimate cannot be negative.",
            )
        if subsidy_estimate > q.gross_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subsidy estimate ({subsidy_estimate}) cannot exceed gross amount ({q.gross_amount}).",
            )
        if subsidy_estimate != standard_subsidy:
            if not payload.subsidy_override_reason or len(payload.subsidy_override_reason.strip()) < 3:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Explicit subsidy_override_reason (at least 3 characters) is required when overriding the standard subsidy policy estimate.",
                )
            subsidy_override_occurred = True
        q.subsidy_estimate = subsidy_estimate
    else:
        # Re-verify existing subsidy does not exceed updated gross amount
        if q.subsidy_estimate > q.gross_amount:
            q.subsidy_estimate = q.gross_amount

    q.net_payable_amount = quantize_amount(max(Decimal("0.00"), q.gross_amount - q.subsidy_estimate))

    # 5. Audit log
    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="QUOTATION_UPDATED",
        entity_id=q.id,
        details={
            "quotation_number": q.quotation_number,
            "version": q.version,
            "gross_amount": float(q.gross_amount),
            "net_payable_amount": float(q.net_payable_amount),
        },
    )

    if subsidy_override_occurred:
        _record_audit_log(
            db=db,
            user_id=current_user.id,
            action="SUBSIDY_OVERRIDDEN",
            entity_id=q.id,
            details={
                "previous_amount": float(standard_subsidy),
                "new_amount": float(q.subsidy_estimate),
                "reason": payload.subsidy_override_reason.strip(),
                "quotation_number": q.quotation_number,
            },
        )

    db.commit()

    # Re-fetch full object
    full_q = db.execute(
        select(Quotation)
        .options(
            selectinload(Quotation.creator),
            selectinload(Quotation.enquiry).selectinload(Enquiry.customer),
            selectinload(Quotation.survey),
            selectinload(Quotation.items).selectinload(QuotationItem.product),
            selectinload(Quotation.revisions).selectinload(QuotationRevision.reviser),
        )
        .where(Quotation.id == q.id)
    ).scalar_one()

    return APIResponse(
        success=True,
        message=f"Quotation {full_q.quotation_number} updated successfully.",
        data=_build_quotation_response(full_q),
    )


@router.post("/{id}/submit", response_model=APIResponse[QuotationResponse])
def submit_quotation_for_approval(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_quotation_update_access),
):
    """
    Submit a DRAFT quotation for internal technical / commercial approval.
    Status transitions from DRAFT -> PENDING_APPROVAL.
    """
    q = db.execute(
        select(Quotation)
        .options(
            selectinload(Quotation.enquiry).selectinload(Enquiry.customer),
            selectinload(Quotation.items),
        )
        .where(Quotation.id == id)
        .with_for_update()
    ).scalar_one_or_none()

    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quotation with ID {id} not found.",
        )

    validate_status_transition(q.status, "PENDING_APPROVAL")

    if not q.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit an empty quotation for approval.",
        )

    q.status = "PENDING_APPROVAL"

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="QUOTATION_SUBMITTED",
        entity_id=q.id,
        details={
            "quotation_number": q.quotation_number,
            "version": q.version,
            "net_payable_amount": float(q.net_payable_amount),
        },
    )

    db.commit()
    db.expire_all()

    full_q = db.execute(
        select(Quotation)
        .options(
            selectinload(Quotation.creator),
            selectinload(Quotation.enquiry).selectinload(Enquiry.customer),
            selectinload(Quotation.survey),
            selectinload(Quotation.items).selectinload(QuotationItem.product),
            selectinload(Quotation.revisions).selectinload(QuotationRevision.reviser),
        )
        .where(Quotation.id == q.id)
    ).scalar_one()

    return APIResponse(
        success=True,
        message=f"Quotation {full_q.quotation_number} submitted for review.",
        data=_build_quotation_response(full_q),
    )


@router.post("/{id}/approve", response_model=APIResponse[QuotationResponse])
def approve_quotation(
    id: int,
    payload: Optional[QuotationApprovalRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_quotation_approve_access),
):
    """
    Approve quotation: PENDING_APPROVAL -> APPROVED.
    Authorized for TECHNICAL_MANAGER, DIRECTOR, and SUPER_ADMIN.
    Strict Rule: Creator cannot approve their own quotation unless SUPER_ADMIN.
    """
    q = db.execute(
        select(Quotation)
        .options(selectinload(Quotation.creator))
        .where(Quotation.id == id)
        .with_for_update()
    ).scalar_one_or_none()

    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quotation with ID {id} not found.",
        )

    # Separation of duties: Creator cannot approve own quotation unless SUPER_ADMIN
    if q.created_by == current_user.id and current_user.role.slug != SystemRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Creators are strictly prohibited from approving their own quotations. Must be reviewed by another authorized manager.",
        )

    validate_status_transition(q.status, "APPROVED")

    q.status = "APPROVED"

    comments = payload.comments if payload else None
    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="QUOTATION_APPROVED",
        entity_id=q.id,
        details={
            "quotation_number": q.quotation_number,
            "version": q.version,
            "approved_by": current_user.id,
            "comments": comments,
        },
    )

    # Notify creator
    if q.created_by != current_user.id:
        _send_notification(
            db=db,
            user_id=q.created_by,
            title="Quotation Approved",
            message=f"Quotation {q.quotation_number} has been approved by {current_user.full_name} and is ready to send to customer.",
            notification_type="APPROVAL",
        )

    db.commit()
    db.expire_all()

    full_q = db.execute(
        select(Quotation)
        .options(
            selectinload(Quotation.creator),
            selectinload(Quotation.enquiry).selectinload(Enquiry.customer),
            selectinload(Quotation.survey),
            selectinload(Quotation.items).selectinload(QuotationItem.product),
            selectinload(Quotation.revisions).selectinload(QuotationRevision.reviser),
        )
        .where(Quotation.id == q.id)
    ).scalar_one()

    return APIResponse(
        success=True,
        message=f"Quotation {full_q.quotation_number} approved successfully.",
        data=_build_quotation_response(full_q),
    )


@router.post("/{id}/reject", response_model=APIResponse[QuotationResponse])
def reject_quotation(
    id: int,
    payload: QuotationRejectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_quotation_approve_access),
):
    """
    Reject quotation during internal review: PENDING_APPROVAL -> REJECTED.
    Requires mandatory rejection comments.
    """
    q = db.execute(
        select(Quotation)
        .options(selectinload(Quotation.creator))
        .where(Quotation.id == id)
        .with_for_update()
    ).scalar_one_or_none()

    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quotation with ID {id} not found.",
        )

    validate_status_transition(q.status, "REJECTED")

    q.status = "REJECTED"

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="QUOTATION_REJECTED",
        entity_id=q.id,
        details={
            "quotation_number": q.quotation_number,
            "version": q.version,
            "rejected_by": current_user.id,
            "comments": payload.comments.strip(),
        },
    )

    # Notify creator
    if q.created_by != current_user.id:
        _send_notification(
            db=db,
            user_id=q.created_by,
            title="Quotation Rejected",
            message=f"Quotation {q.quotation_number} was rejected by {current_user.full_name}: {payload.comments.strip()}",
            notification_type="SYSTEM",
        )

    db.commit()
    db.expire_all()

    full_q = db.execute(
        select(Quotation)
        .options(
            selectinload(Quotation.creator),
            selectinload(Quotation.enquiry).selectinload(Enquiry.customer),
            selectinload(Quotation.survey),
            selectinload(Quotation.items).selectinload(QuotationItem.product),
            selectinload(Quotation.revisions).selectinload(QuotationRevision.reviser),
        )
        .where(Quotation.id == q.id)
    ).scalar_one()

    return APIResponse(
        success=True,
        message=f"Quotation {full_q.quotation_number} has been rejected.",
        data=_build_quotation_response(full_q),
    )


@router.post("/{id}/send", response_model=APIResponse[QuotationResponse])
def send_quotation_to_customer(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_quotation_update_access),
):
    """
    Send an approved quotation to the customer: APPROVED -> SENT.
    Synchronizes enquiry status to 'QUOTED' within the same transaction.
    """
    q = db.execute(
        select(Quotation)
        .options(
            selectinload(Quotation.enquiry).selectinload(Enquiry.customer),
            selectinload(Quotation.items),
        )
        .where(Quotation.id == id)
        .with_for_update()
    ).scalar_one_or_none()

    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quotation with ID {id} not found.",
        )

    validate_status_transition(q.status, "SENT")

    # Validate Enquiry Status
    enquiry = q.enquiry
    if enquiry.status in ("CANCELLED", "LOST"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot dispatch quotation because associated enquiry is in terminal status '{enquiry.status}'.",
        )

    q.status = "SENT"
    enquiry.status = "QUOTED"

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="QUOTATION_SENT",
        entity_id=q.id,
        details={
            "quotation_number": q.quotation_number,
            "version": q.version,
            "sent_to_customer_id": enquiry.customer_id,
            "enquiry_status_updated_to": "QUOTED",
        },
    )

    db.commit()
    db.expire_all()

    full_q = db.execute(
        select(Quotation)
        .options(
            selectinload(Quotation.creator),
            selectinload(Quotation.enquiry).selectinload(Enquiry.customer),
            selectinload(Quotation.survey),
            selectinload(Quotation.items).selectinload(QuotationItem.product),
            selectinload(Quotation.revisions).selectinload(QuotationRevision.reviser),
        )
        .where(Quotation.id == q.id)
    ).scalar_one()

    return APIResponse(
        success=True,
        message=f"Quotation {full_q.quotation_number} sent to customer. Enquiry updated to QUOTED.",
        data=_build_quotation_response(full_q),
    )


@router.post("/{id}/accept", response_model=APIResponse[QuotationResponse])
def customer_accept_quotation(
    id: int,
    payload: Optional[QuotationCustomerAcceptRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Customer accepts quotation: SENT -> ACCEPTED.
    Enforces customer ownership verification.
    Synchronizes associated enquiry status to 'WON' in the same transaction.
    Row-level locking protects against concurrent or duplicate acceptance.
    """
    q = db.execute(
        select(Quotation)
        .options(
            selectinload(Quotation.enquiry).selectinload(Enquiry.customer),
            selectinload(Quotation.items),
        )
        .where(Quotation.id == id)
        .with_for_update()
    ).scalar_one_or_none()

    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quotation with ID {id} not found.",
        )

    # Customer verification: Must be the customer whose enquiry is quoted, OR Super Admin
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        customer = _get_customer_for_user(current_user, db)
        if not customer or q.enquiry.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only accept quotations associated with your own account.",
            )
    elif current_user.role and current_user.role.slug != SystemRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quotation acceptance must be performed by the authenticated customer.",
        )

    if q.status == "ACCEPTED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This quotation has already been accepted and confirmed.",
        )

    if q.status != "SENT":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Only SENT quotations can be accepted by the customer. Current status is '{q.status}'.",
        )

    # 2. Acquire exclusive row-level lock on parent enquiry to serialize concurrent acceptance attempts for this enquiry
    enquiry = db.execute(
        select(Enquiry)
        .options(selectinload(Enquiry.customer))
        .where(Enquiry.id == q.enquiry_id)
        .with_for_update()
    ).scalar_one_or_none()

    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Associated enquiry with ID {q.enquiry_id} not found.",
        )

    if enquiry.status in ("CANCELLED", "LOST"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot accept quotation because associated enquiry is in terminal status '{enquiry.status}'.",
        )

    # 3. Strict single-acceptance guard: verify no other quotation for this enquiry is already ACCEPTED
    existing_accepted = db.execute(
        select(Quotation.id, Quotation.quotation_number)
        .where(
            Quotation.enquiry_id == q.enquiry_id,
            Quotation.status == "ACCEPTED",
            Quotation.id != q.id,
        )
    ).first()

    if existing_accepted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot accept quotation '{q.quotation_number}'. Another quotation ('{existing_accepted.quotation_number}') for this enquiry has already been accepted. At most one quotation per enquiry may be accepted.",
        )

    if enquiry.status == "WON":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot accept quotation because associated enquiry is already in 'WON' status.",
        )

    q.status = "ACCEPTED"
    enquiry.status = "WON"

    notes = payload.acceptance_notes if payload else None
    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="QUOTATION_ACCEPTED",
        entity_id=q.id,
        details={
            "quotation_number": q.quotation_number,
            "version": q.version,
            "accepted_by_user_id": current_user.id,
            "customer_id": enquiry.customer_id,
            "notes": notes,
            "enquiry_status_updated_to": "WON",
        },
    )

    # Notify sales creator
    _send_notification(
        db=db,
        user_id=q.created_by,
        title="Quotation Accepted!",
        message=f"Quotation {q.quotation_number} has been accepted by customer {enquiry.customer.full_name}! Enquiry marked as WON.",
        notification_type="STATUS_CHANGE",
    )

    db.commit()
    db.expire_all()

    full_q = db.execute(
        select(Quotation)
        .options(
            selectinload(Quotation.creator),
            selectinload(Quotation.enquiry).selectinload(Enquiry.customer),
            selectinload(Quotation.survey),
            selectinload(Quotation.items).selectinload(QuotationItem.product),
            selectinload(Quotation.revisions).selectinload(QuotationRevision.reviser),
        )
        .where(Quotation.id == q.id)
    ).scalar_one()

    return APIResponse(
        success=True,
        message=f"Quotation {full_q.quotation_number} accepted successfully. Deal marked as WON!",
        data=_build_quotation_response(full_q),
    )


@router.post("/{id}/customer-reject", response_model=APIResponse[QuotationResponse])
def customer_reject_quotation(
    id: int,
    payload: QuotationCustomerRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Customer declines quotation: SENT -> REJECTED.
    Requires customer ownership and mandatory rejection reason.
    """
    q = db.execute(
        select(Quotation)
        .options(
            selectinload(Quotation.enquiry).selectinload(Enquiry.customer),
            selectinload(Quotation.items),
        )
        .where(Quotation.id == id)
        .with_for_update()
    ).scalar_one_or_none()

    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quotation with ID {id} not found.",
        )

    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        customer = _get_customer_for_user(current_user, db)
        if not customer or q.enquiry.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only decline quotations associated with your own account.",
            )
    elif current_user.role and current_user.role.slug != SystemRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quotation rejection must be performed by the authenticated customer.",
        )

    if q.status != "SENT":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Only SENT quotations can be declined. Current status is '{q.status}'.",
        )

    q.status = "REJECTED"

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="QUOTATION_REJECTED",
        entity_id=q.id,
        details={
            "quotation_number": q.quotation_number,
            "version": q.version,
            "customer_id": q.enquiry.customer_id,
            "rejection_reason": payload.rejection_reason.strip(),
        },
    )

    # Notify creator
    _send_notification(
        db=db,
        user_id=q.created_by,
        title="Quotation Declined by Customer",
        message=f"Customer declined Quotation {q.quotation_number}: {payload.rejection_reason.strip()}",
        notification_type="STATUS_CHANGE",
    )

    db.commit()
    db.expire_all()

    full_q = db.execute(
        select(Quotation)
        .options(
            selectinload(Quotation.creator),
            selectinload(Quotation.enquiry).selectinload(Enquiry.customer),
            selectinload(Quotation.survey),
            selectinload(Quotation.items).selectinload(QuotationItem.product),
            selectinload(Quotation.revisions).selectinload(QuotationRevision.reviser),
        )
        .where(Quotation.id == q.id)
    ).scalar_one()

    return APIResponse(
        success=True,
        message=f"Quotation {full_q.quotation_number} declined.",
        data=_build_quotation_response(full_q),
    )


@router.post("/{id}/revise", response_model=APIResponse[QuotationResponse])
def revise_quotation(
    id: int,
    payload: QuotationRevisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_quotation_update_access),
):
    """
    Create a new revision for a quotation.
    1. Snapshots existing quotation state and line items to `quotation_revisions`.
    2. Increments quotation.version.
    3. Returns active quotation to DRAFT status.
    4. Applies updated items/costs/subsidy if supplied in request.
    Strict Rule: ACCEPTED quotations cannot be revised.
    """
    if current_user.role and current_user.role.slug in (SystemRole.TECHNICAL_MANAGER, SystemRole.DIRECTOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Technical Managers and Directors cannot initiate quotation revisions with sales pricing.",
        )

    q = db.execute(
        select(Quotation)
        .options(
            selectinload(Quotation.enquiry).selectinload(Enquiry.customer),
            selectinload(Quotation.items).selectinload(QuotationItem.product),
            selectinload(Quotation.revisions),
        )
        .where(Quotation.id == id)
        .with_for_update()
    ).scalar_one_or_none()

    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quotation with ID {id} not found.",
        )

    if q.status == "ACCEPTED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ACCEPTED quotations are legally binding and cannot be revised.",
        )

    if q.status == "PENDING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Quotation is currently under review. Wait for approval/rejection before revising.",
        )

    # 1. Build snapshot dictionary of previous state
    snapshot_items = [
        {
            "product_id": item.product_id,
            "product_code": item.product.product_code if item.product else None,
            "product_name": item.product.name if item.product else None,
            "item_description": item.item_description,
            "quantity": float(item.quantity),
            "unit_price": float(item.unit_price),
            "discount_amount": float(item.discount_amount),
            "tax_rate_percent": float(item.tax_rate_percent),
            "total_amount": float(item.total_amount),
        }
        for item in q.items
    ]

    snapshot = {
        "quotation_number": q.quotation_number,
        "version": q.version,
        "system_type": q.system_type,
        "capacity_kw": float(q.capacity_kw),
        "total_product_cost": float(q.total_product_cost),
        "installation_cost": float(q.installation_cost),
        "tax_amount": float(q.tax_amount),
        "gross_amount": float(q.gross_amount),
        "subsidy_estimate": float(q.subsidy_estimate),
        "net_payable_amount": float(q.net_payable_amount),
        "status": q.status,
        "valid_until": q.valid_until.isoformat() if q.valid_until else None,
        "quotation_date": q.quotation_date.isoformat() if q.quotation_date else None,
        "terms_and_conditions": q.terms_and_conditions,
        "created_by": q.created_by,
        "items": snapshot_items,
    }

    # 2. Record Revision Snapshot
    revision = QuotationRevision(
        quotation_id=q.id,
        revision_number=q.version,
        snapshot_data=snapshot,
        reason_for_revision=payload.reason_for_revision.strip(),
        revised_by=current_user.id,
    )
    q.revisions.append(revision)

    # 3. Increment version and return active quotation to DRAFT
    q.version += 1
    q.status = "DRAFT"

    # 4. Apply optional updates to active quotation
    if payload.system_type is not None:
        q.system_type = payload.system_type
    if payload.capacity_kw is not None:
        if payload.capacity_kw <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="capacity_kw must be strictly greater than zero.",
            )
        q.capacity_kw = quantize_amount(payload.capacity_kw)
    if payload.terms_and_conditions is not None:
        q.terms_and_conditions = payload.terms_and_conditions
    if payload.valid_until is not None:
        if payload.valid_until < q.quotation_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"valid_until ({payload.valid_until}) must be on or after quotation_date ({q.quotation_date}).",
            )
        q.valid_until = payload.valid_until
    if payload.installation_cost is not None:
        q.installation_cost = quantize_amount(payload.installation_cost)

    # 5. Apply updated items if provided
    if payload.items is not None:
        if not payload.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quotation must contain at least one line item.",
            )

        q.items.clear()
        total_discounted_base = Decimal("0.00")
        total_tax_amount = Decimal("0.00")

        for item_in in payload.items:
            product = db.execute(select(Product).where(Product.id == item_in.product_id)).scalar_one_or_none()
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {item_in.product_id} not found.",
                )
            if not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{product.name}' ({product.product_code}) is inactive and cannot be added.",
                )

            unit_price = item_in.unit_price if item_in.unit_price is not None else product.base_price
            tax_rate = item_in.tax_rate_percent if item_in.tax_rate_percent is not None else product.tax_rate_percent
            desc = item_in.item_description or product.name

            base_amt, disc_base, tax, line_total = calculate_line_item(
                quantity=item_in.quantity,
                unit_price=unit_price,
                discount_amount=item_in.discount_amount,
                tax_rate_percent=tax_rate,
            )

            new_item = QuotationItem(
                quotation_id=q.id,
                product_id=product.id,
                item_description=desc,
                quantity=quantize_amount(item_in.quantity),
                unit_price=quantize_amount(unit_price),
                discount_amount=quantize_amount(item_in.discount_amount),
                tax_rate_percent=quantize_amount(tax_rate),
                total_amount=quantize_amount(line_total),
            )
            q.items.append(new_item)
            total_discounted_base += disc_base
            total_tax_amount += tax

        q.total_product_cost = quantize_amount(total_discounted_base)
        q.tax_amount = quantize_amount(total_tax_amount)

    # 6. Recalculate totals
    q.gross_amount = quantize_amount(q.total_product_cost + q.installation_cost + q.tax_amount)

    # 7. Subsidy Policy & Override
    customer_type = q.enquiry.customer.customer_type if (q.enquiry and q.enquiry.customer) else "RESIDENTIAL"
    standard_subsidy = compute_standard_subsidy_policy(customer_type, q.capacity_kw)

    subsidy_override_occurred = False
    if payload.subsidy_estimate is not None:
        subsidy_estimate = quantize_amount(payload.subsidy_estimate)
        if subsidy_estimate < Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subsidy estimate cannot be negative.",
            )
        if subsidy_estimate > q.gross_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subsidy estimate ({subsidy_estimate}) cannot exceed gross amount ({q.gross_amount}).",
            )
        if subsidy_estimate != standard_subsidy:
            if not payload.subsidy_override_reason or len(payload.subsidy_override_reason.strip()) < 3:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Explicit subsidy_override_reason is required when overriding the standard subsidy policy estimate.",
                )
            subsidy_override_occurred = True
        q.subsidy_estimate = subsidy_estimate
    else:
        if q.subsidy_estimate > q.gross_amount:
            q.subsidy_estimate = q.gross_amount

    q.net_payable_amount = quantize_amount(max(Decimal("0.00"), q.gross_amount - q.subsidy_estimate))

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="QUOTATION_REVISED",
        entity_id=q.id,
        details={
            "quotation_number": q.quotation_number,
            "new_version": q.version,
            "revision_number": revision.revision_number,
            "reason": payload.reason_for_revision.strip(),
            "gross_amount": float(q.gross_amount),
            "net_payable_amount": float(q.net_payable_amount),
        },
    )

    if subsidy_override_occurred:
        _record_audit_log(
            db=db,
            user_id=current_user.id,
            action="SUBSIDY_OVERRIDDEN",
            entity_id=q.id,
            details={
                "previous_amount": float(standard_subsidy),
                "new_amount": float(q.subsidy_estimate),
                "reason": payload.subsidy_override_reason.strip(),
                "quotation_number": q.quotation_number,
            },
        )

    db.commit()
    db.expire_all()

    full_q = db.execute(
        select(Quotation)
        .options(
            selectinload(Quotation.creator),
            selectinload(Quotation.enquiry).selectinload(Enquiry.customer),
            selectinload(Quotation.survey),
            selectinload(Quotation.items).selectinload(QuotationItem.product),
            selectinload(Quotation.revisions).selectinload(QuotationRevision.reviser),
        )
        .where(Quotation.id == q.id)
    ).scalar_one()

    return APIResponse(
        success=True,
        message=f"Quotation {full_q.quotation_number} revised to version {full_q.version} (returned to DRAFT).",
        data=_build_quotation_response(full_q),
    )


@router.delete("/{id}", response_model=APIResponse[dict])
def delete_draft_quotation(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_quotation_update_access),
):
    """
    Delete a DRAFT quotation. Only DRAFT quotations can be deleted.
    """
    q = db.execute(select(Quotation).where(Quotation.id == id).with_for_update()).scalar_one_or_none()
    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quotation with ID {id} not found.",
        )

    if q.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete quotation in status '{q.status}'. Only DRAFT quotations can be deleted.",
        )

    quo_num = q.quotation_number
    db.delete(q)

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="QUOTATION_DELETED",
        entity_id=id,
        details={"quotation_number": quo_num},
    )

    db.commit()

    return APIResponse(
        success=True,
        message=f"Quotation {quo_num} deleted successfully.",
        data={"id": id, "quotation_number": quo_num},
    )
