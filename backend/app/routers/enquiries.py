from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, date
import math
import secrets

from app.database import get_db
from app.models.crm import Customer, Enquiry, Followup
from app.models.auth import User, Employee
from app.schemas.crm import (
    EnquiryCreate,
    EnquiryUpdate,
    EnquiryStatusUpdate,
    EnquiryAssignUpdate,
    EnquiryResponse,
    EnquiryListResponse,
    VALID_ENQUIRY_STATUSES,
)
from app.schemas import APIResponse
from app.dependencies.auth import get_current_user, require_permissions, get_user_permissions
from app.utils.roles import SystemRole

router = APIRouter(prefix="/enquiries", tags=["Enquiry & Pipeline Management"])


def require_enquiry_read_access(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role and current_user.role.slug in (SystemRole.SUPER_ADMIN, SystemRole.DIRECTOR, SystemRole.CUSTOMER):
        return current_user
    perms = get_user_permissions(current_user)
    if "enquiries.read" in perms:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions to view enquiries",
    )


def require_enquiry_create_access(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role and current_user.role.slug in (SystemRole.SUPER_ADMIN, SystemRole.DIRECTOR, SystemRole.CUSTOMER):
        return current_user
    perms = get_user_permissions(current_user)
    if "enquiries.create" in perms:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions to create enquiries",
    )


def require_enquiry_update_access(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role and current_user.role.slug in (SystemRole.SUPER_ADMIN, SystemRole.DIRECTOR):
        return current_user
    perms = get_user_permissions(current_user)
    if "enquiries.update" in perms:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions to update or reassign enquiries",
    )


def _get_employee_for_user(user: User, db: Session) -> Optional[Employee]:
    return db.execute(
        select(Employee).where(Employee.user_id == user.id)
    ).scalar_one_or_none()


def _generate_enquiry_number(db: Session) -> str:
    today_str = date.today().strftime("%Y%m%d")
    for _ in range(10):
        suffix = secrets.token_hex(2).upper()
        candidate = f"ENQ-{today_str}-{suffix}"
        exists = db.execute(select(Enquiry.id).where(Enquiry.enquiry_number == candidate)).scalar_one_or_none()
        if not exists:
            return candidate
    # Fallback with timestamp microsecond
    return f"ENQ-{today_str}-{int(datetime.now().timestamp()) % 10000:04d}"


def _validate_capacity_for_customer(customer: Customer, capacity_kw: float) -> None:
    c_type = (customer.customer_type or "RESIDENTIAL").strip().upper()
    if c_type == "RESIDENTIAL":
        if capacity_kw < 1.0 or capacity_kw > 5.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Residential rooftop solar capacity must be between 1.0 kW and 5.0 kW. Provided: {capacity_kw} kW",
            )
    elif c_type in ("COMMERCIAL", "INDUSTRIAL"):
        if capacity_kw <= 0.0 or capacity_kw > 500.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{c_type.capitalize()} solar capacity must be greater than 0 kW and up to 500.0 kW. Provided: {capacity_kw} kW",
            )
    else:
        if capacity_kw <= 0.0 or capacity_kw > 500.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Solar capacity must be greater than 0 kW and up to 500.0 kW. Provided: {capacity_kw} kW",
            )


def _build_enquiry_response(enq: Enquiry, db: Session) -> EnquiryResponse:
    cust_name = None
    cust_phone = None
    cust_city = None
    if enq.customer:
        cust_name = enq.customer.full_name
        cust_phone = enq.customer.phone
        cust_city = enq.customer.city

    sales_name = None
    sales_code = None
    if enq.assigned_sales:
        sales_code = enq.assigned_sales.employee_code
        if enq.assigned_sales.user:
            sales_name = enq.assigned_sales.user.full_name

    # Followup statistics
    followup_stats = db.execute(
        select(
            func.count(Followup.id),
            func.max(Followup.scheduled_at),
        ).where(Followup.enquiry_id == enq.id)
    ).first()

    followup_count = followup_stats[0] if followup_stats else 0
    latest_followup = followup_stats[1] if followup_stats else None

    return EnquiryResponse(
        id=enq.id,
        customer_id=enq.customer_id,
        customer_name=cust_name,
        customer_phone=cust_phone,
        customer_city=cust_city,
        enquiry_number=enq.enquiry_number,
        source=enq.source,
        system_type=enq.system_type,
        proposed_capacity_kw=float(enq.proposed_capacity_kw),
        monthly_electricity_bill=float(enq.monthly_electricity_bill) if enq.monthly_electricity_bill is not None else None,
        roof_type=enq.roof_type,
        status=enq.status,
        assigned_sales_id=enq.assigned_sales_id,
        assigned_sales_name=sales_name,
        assigned_sales_code=sales_code,
        notes=enq.notes,
        followup_count=followup_count,
        latest_followup_date=latest_followup,
        created_at=enq.created_at,
        updated_at=enq.updated_at,
    )


@router.get("", response_model=APIResponse[EnquiryListResponse])
def list_enquiries(
    search: Optional[str] = Query(None, description="Search by enquiry number, notes, customer name or phone"),
    status: Optional[str] = Query(None, description="Filter by status (NEW, CONTACTED, SURVEY_REQUESTED, QUOTED, WON, LOST, CANCELLED)"),
    system_type: Optional[str] = Query(None, description="Filter by system type (ON_GRID, OFF_GRID, HYBRID)"),
    source: Optional[str] = Query(None, description="Filter by enquiry source"),
    assigned_sales_id: Optional[int] = Query(None, description="Filter by assigned sales employee ID"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_enquiry_read_access),
):
    """
    List enquiries with filtering by pipeline status, system type, source, and sales assignment.
    Enforces sales data isolation for SALES role users and customer scoping for CUSTOMER role.
    """
    stmt = select(Enquiry).options(
        selectinload(Enquiry.customer),
        selectinload(Enquiry.assigned_sales).selectinload(Employee.user),
    )

    # Customer Data Scoping
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        cust = db.execute(select(Customer).where(Customer.user_id == current_user.id)).scalar_one_or_none()
        if not cust:
            return APIResponse(
                success=True,
                message="No enquiries found",
                data=EnquiryListResponse(items=[], total=0, page=page, limit=limit, total_pages=0),
            )
        stmt = stmt.where(Enquiry.customer_id == cust.id)

    # 1. SALES Data Isolation:
    if current_user.role and current_user.role.slug == SystemRole.SALES:
        emp = _get_employee_for_user(current_user, db)
        if not emp:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sales user is not linked to an active employee record",
            )
        if assigned_sales_id is not None and assigned_sales_id != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sales representatives can only view enquiries within their authorized assignment scope",
            )
        # Only view leads assigned to this employee or unassigned leads
        stmt = stmt.where(
            or_(
                Enquiry.assigned_sales_id == emp.id,
                Enquiry.assigned_sales_id.is_(None),
            )
        )
    elif assigned_sales_id is not None:
        stmt = stmt.where(Enquiry.assigned_sales_id == assigned_sales_id)

    if customer_id:
        stmt = stmt.where(Enquiry.customer_id == customer_id)

    if status:
        clean_status = status.strip().upper()
        stmt = stmt.where(Enquiry.status == clean_status)

    if system_type:
        clean_sys = system_type.strip().upper()
        stmt = stmt.where(Enquiry.system_type == clean_sys)

    if source:
        clean_src = source.strip().upper()
        stmt = stmt.where(Enquiry.source == clean_src)

    if search:
        term = f"%{search.strip().lower()}%"
        stmt = stmt.join(Enquiry.customer).where(
            or_(
                func.lower(Enquiry.enquiry_number).like(term),
                func.lower(Enquiry.notes).like(term),
                func.lower(Customer.full_name).like(term),
                func.lower(Customer.phone).like(term),
                func.lower(Customer.city).like(term),
            )
        )

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar() or 0

    stmt = stmt.order_by(Enquiry.created_at.desc()).offset((page - 1) * limit).limit(limit)
    enquiries = db.execute(stmt).scalars().all()

    items = [_build_enquiry_response(e, db) for e in enquiries]
    total_pages = math.ceil(total / limit) if total > 0 else 1

    return APIResponse(
        success=True,
        message="Enquiries retrieved successfully",
        data=EnquiryListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        ),
    )


@router.post("", response_model=APIResponse[EnquiryResponse], status_code=status.HTTP_201_CREATED)
def create_enquiry(
    payload: EnquiryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_enquiry_create_access),
):
    """
    Create a new enquiry linked to an existing customer.
    Enforces customer-type-specific capacity constraints and safe retry on concurrency conflicts.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        cust = db.execute(select(Customer).where(Customer.user_id == current_user.id)).scalar_one_or_none()
        if not cust:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer profile not linked to authenticated user",
            )
        target_customer_id = cust.id
        payload_source = "CUSTOMER_PORTAL"
        assigned_sales_id = None
        customer = cust
    else:
        target_customer_id = payload.customer_id
        payload_source = payload.source or "DIRECT"
        # Validate customer exists
        customer = db.execute(
            select(Customer).where(Customer.id == target_customer_id)
        ).scalar_one_or_none()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer ID {target_customer_id} does not exist",
            )

        if not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create enquiry for an inactive customer record",
            )

        # Validate assigned_sales_id
        assigned_sales_id = payload.assigned_sales_id
        if current_user.role and current_user.role.slug == SystemRole.SALES:
            emp = _get_employee_for_user(current_user, db)
            if not emp:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sales user is not linked to an active employee record",
                )
            # Sales rep creating an enquiry can assign to themselves or leave unassigned
            if assigned_sales_id is not None and assigned_sales_id != emp.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sales representatives cannot assign new enquiries to another representative",
                )
            if assigned_sales_id is None:
                # Default assignment to creating sales rep
                assigned_sales_id = emp.id
        elif assigned_sales_id is not None:
            sales_emp = db.execute(
                select(Employee).where(Employee.id == assigned_sales_id)
            ).scalar_one_or_none()
            if not sales_emp:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Assigned sales employee ID {assigned_sales_id} not found",
                )
            if not sales_emp.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Employee {sales_emp.employee_code} is inactive and cannot be assigned enquiries",
                )

    # Validate customer-type-specific capacity
    _validate_capacity_for_customer(customer, payload.proposed_capacity_kw)

    # Concurrency-safe creation with retry on duplicate enquiry_number conflict
    max_retries = 3
    enquiry = None
    for attempt in range(max_retries):
        enq_number = _generate_enquiry_number(db)
        enquiry = Enquiry(
            customer_id=target_customer_id,
            enquiry_number=enq_number,
            source=payload_source,
            system_type=payload.system_type,
            proposed_capacity_kw=payload.proposed_capacity_kw,
            monthly_electricity_bill=payload.monthly_electricity_bill,
            roof_type=payload.roof_type,
            status="NEW",
            assigned_sales_id=assigned_sales_id,
            notes=payload.notes,
        )
        db.add(enquiry)
        try:
            db.commit()
            db.refresh(enquiry)
            break
        except IntegrityError as exc:
            db.rollback()
            err_str = str(exc).lower()
            if "enquiry_number" in err_str or "uq_enquiries_enquiry_number" in err_str or "unique" in err_str:
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Unable to generate a unique enquiry number after multiple attempts. Please retry.",
                    )
                continue
            # Raise other unexpected integrity errors without retrying
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database integrity conflict during enquiry creation: {str(exc.orig) if hasattr(exc, 'orig') else str(exc)}",
            )

    # Eager load customer & assigned employee
    enquiry = db.execute(
        select(Enquiry)
        .where(Enquiry.id == enquiry.id)
        .options(
            selectinload(Enquiry.customer),
            selectinload(Enquiry.assigned_sales).selectinload(Employee.user),
        )
    ).scalar_one()

    return APIResponse(
        success=True,
        message="Enquiry created successfully",
        data=_build_enquiry_response(enquiry, db),
    )


@router.get("/{enquiry_id}", response_model=APIResponse[EnquiryResponse])
def get_enquiry(
    enquiry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_enquiry_read_access),
):
    """
    Get detailed enquiry record.
    Enforces sales data isolation.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        enquiry = db.execute(
            select(Enquiry)
            .join(Enquiry.customer)
            .where(Enquiry.id == enquiry_id, Customer.user_id == current_user.id)
            .options(
                selectinload(Enquiry.customer),
                selectinload(Enquiry.assigned_sales).selectinload(Employee.user),
            )
        ).scalar_one_or_none()
        if not enquiry:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this enquiry",
            )
        return APIResponse(
            success=True,
            message="Enquiry retrieved successfully",
            data=_build_enquiry_response(enquiry, db),
        )

    enquiry = db.execute(
        select(Enquiry)
        .where(Enquiry.id == enquiry_id)
        .options(
            selectinload(Enquiry.customer),
            selectinload(Enquiry.assigned_sales).selectinload(Employee.user),
        )
    ).scalar_one_or_none()
    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enquiry with ID {enquiry_id} not found",
        )

    # SALES Isolation: Cannot view another representative's assigned enquiry
    if current_user.role and current_user.role.slug == SystemRole.SALES:
        emp = _get_employee_for_user(current_user, db)
        if not emp or (enquiry.assigned_sales_id is not None and enquiry.assigned_sales_id != emp.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access an enquiry assigned to another sales representative",
            )

    return APIResponse(
        success=True,
        message="Enquiry retrieved successfully",
        data=_build_enquiry_response(enquiry, db),
    )


@router.put("/{enquiry_id}", response_model=APIResponse[EnquiryResponse])
def update_enquiry(
    enquiry_id: int,
    payload: EnquiryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_enquiry_update_access),
):
    """
    Update enquiry details.
    Enforces ownership check and customer-type-specific capacity validation.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot modify sales enquiries",
        )

    enquiry = db.execute(
        select(Enquiry)
        .where(Enquiry.id == enquiry_id)
        .options(
            selectinload(Enquiry.customer),
            selectinload(Enquiry.assigned_sales).selectinload(Employee.user),
        )
    ).scalar_one_or_none()
    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enquiry with ID {enquiry_id} not found",
        )

    # SALES Isolation check:
    if current_user.role and current_user.role.slug == SystemRole.SALES:
        emp = _get_employee_for_user(current_user, db)
        if not emp or (enquiry.assigned_sales_id is not None and enquiry.assigned_sales_id != emp.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify an enquiry assigned to another sales representative",
            )

    # Customer-type capacity validation if updating proposed_capacity_kw
    if payload.proposed_capacity_kw is not None:
        _validate_capacity_for_customer(enquiry.customer, payload.proposed_capacity_kw)
        enquiry.proposed_capacity_kw = payload.proposed_capacity_kw

    # Reassignment rule:
    if payload.assigned_sales_id is not None:
        if current_user.role and current_user.role.slug == SystemRole.SALES:
            emp = _get_employee_for_user(current_user, db)
            if not emp or (payload.assigned_sales_id != emp.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Sales representatives cannot reassign enquiries to other representatives",
                )
        else:
            sales_emp = db.execute(
                select(Employee).where(Employee.id == payload.assigned_sales_id)
            ).scalar_one_or_none()
            if not sales_emp:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Assigned sales employee ID {payload.assigned_sales_id} not found",
                )
            enquiry.assigned_sales_id = payload.assigned_sales_id

    if payload.source is not None:
        enquiry.source = payload.source
    if payload.system_type is not None:
        enquiry.system_type = payload.system_type
    if payload.monthly_electricity_bill is not None:
        enquiry.monthly_electricity_bill = payload.monthly_electricity_bill
    if payload.roof_type is not None:
        enquiry.roof_type = payload.roof_type
    if payload.notes is not None:
        enquiry.notes = payload.notes

    enquiry.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(enquiry)

    return APIResponse(
        success=True,
        message="Enquiry updated successfully",
        data=_build_enquiry_response(enquiry, db),
    )


@router.put("/{enquiry_id}/status", response_model=APIResponse[EnquiryResponse])
def update_enquiry_status(
    enquiry_id: int,
    payload: EnquiryStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_enquiry_update_access),
):
    """
    Advance enquiry through sales pipeline stages.
    Enforces sales ownership.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot change enquiry pipeline status",
        )

    enquiry = db.execute(
        select(Enquiry)
        .where(Enquiry.id == enquiry_id)
        .options(
            selectinload(Enquiry.customer),
            selectinload(Enquiry.assigned_sales).selectinload(Employee.user),
        )
    ).scalar_one_or_none()
    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enquiry with ID {enquiry_id} not found",
        )

    # SALES Isolation check:
    if current_user.role and current_user.role.slug == SystemRole.SALES:
        emp = _get_employee_for_user(current_user, db)
        if not emp or (enquiry.assigned_sales_id is not None and enquiry.assigned_sales_id != emp.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update status of an enquiry assigned to another sales representative",
            )

    new_status = payload.status.strip().upper()

    if new_status == "SURVEY_REQUESTED":
        if not enquiry.proposed_capacity_kw or float(enquiry.proposed_capacity_kw) <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Enquiry requires a valid proposed solar capacity (kW) before requesting a site survey",
            )
        if not enquiry.customer or not enquiry.customer.address or not enquiry.customer.city:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer address and city must be complete before requesting a site survey",
            )

    enquiry.status = new_status
    if payload.notes:
        existing_notes = enquiry.notes or ""
        timestamp_prefix = datetime.now().strftime("%Y-%m-%d %H:%M")
        enquiry.notes = f"{existing_notes}\n[{timestamp_prefix} Status -> {new_status}]: {payload.notes}".strip()

    enquiry.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(enquiry)

    return APIResponse(
        success=True,
        message=f"Enquiry status updated to {new_status}",
        data=_build_enquiry_response(enquiry, db),
    )


@router.put("/{enquiry_id}/assign", response_model=APIResponse[EnquiryResponse])
def assign_enquiry_sales_rep(
    enquiry_id: int,
    payload: EnquiryAssignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_enquiry_update_access),
):
    """
    Assign or reassign an enquiry to a sales representative.
    Restricted to SUPER_ADMIN and DIRECTOR for reassignment; SALES users can only self-assign unassigned enquiries.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot assign sales representatives",
        )

    enquiry = db.execute(
        select(Enquiry)
        .where(Enquiry.id == enquiry_id)
        .options(
            selectinload(Enquiry.customer),
            selectinload(Enquiry.assigned_sales).selectinload(Employee.user),
        )
    ).scalar_one_or_none()
    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enquiry with ID {enquiry_id} not found",
        )

    # Role-based assignment rules:
    if current_user.role and current_user.role.slug == SystemRole.SALES:
        emp = _get_employee_for_user(current_user, db)
        if not emp:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sales user is not linked to an active employee record",
            )
        # If enquiry is already assigned to someone else, SALES cannot touch it
        if enquiry.assigned_sales_id is not None and enquiry.assigned_sales_id != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Reassignment of another representative's enquiry is restricted to Super Admin and Director",
            )
        # SALES can only self-assign (claim) unassigned enquiries
        if payload.assigned_sales_id != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sales representatives can only self-assign enquiries to themselves",
            )
        enquiry.assigned_sales_id = emp.id
    else:
        # SUPER_ADMIN and DIRECTOR have full reassignment privileges
        if payload.assigned_sales_id is not None:
            sales_emp = db.execute(
                select(Employee).where(Employee.id == payload.assigned_sales_id)
            ).scalar_one_or_none()
            if not sales_emp:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Sales employee ID {payload.assigned_sales_id} not found",
                )
            if not sales_emp.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Employee {sales_emp.employee_code} is inactive and cannot be assigned enquiries",
                )
            enquiry.assigned_sales_id = payload.assigned_sales_id
        else:
            enquiry.assigned_sales_id = None

    enquiry.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(enquiry)

    return APIResponse(
        success=True,
        message="Enquiry assignment updated successfully",
        data=_build_enquiry_response(enquiry, db),
    )
