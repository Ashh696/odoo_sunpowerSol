from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_
from datetime import datetime, timezone
import math

from app.database import get_db
from app.models.crm import Customer, Enquiry, Followup
from app.models.auth import User, Employee
from app.schemas.crm import (
    FollowupCreate,
    FollowupComplete,
    FollowupReschedule,
    FollowupResponse,
    FollowupListResponse,
)
from app.schemas import APIResponse
from app.dependencies.auth import get_current_user, require_permissions, get_user_permissions
from app.utils.roles import SystemRole

router = APIRouter(prefix="/followups", tags=["Followup & Touchpoint Management"])


def require_followup_access(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role and current_user.role.slug in (SystemRole.SUPER_ADMIN, SystemRole.DIRECTOR):
        return current_user
    perms = get_user_permissions(current_user)
    if "followups.manage" in perms:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions to access follow-ups",
    )


def _get_employee_for_user(user: User, db: Session) -> Optional[Employee]:
    return db.execute(
        select(Employee).where(Employee.user_id == user.id)
    ).scalar_one_or_none()


def _build_followup_response(f: Followup) -> FollowupResponse:
    now_utc = datetime.now(timezone.utc)
    is_overdue = False
    if f.status == "SCHEDULED" and f.scheduled_at:
        if f.scheduled_at < now_utc:
            is_overdue = True

    enq_no = f.enquiry.enquiry_number if f.enquiry else None
    cust_id = f.enquiry.customer_id if f.enquiry else None
    cust_name = None
    if f.enquiry and f.enquiry.customer:
        cust_name = f.enquiry.customer.full_name

    conductor_name = None
    if f.conductor:
        if f.conductor.user:
            conductor_name = f.conductor.user.full_name
        else:
            conductor_name = f.conductor.employee_code

    return FollowupResponse(
        id=f.id,
        enquiry_id=f.enquiry_id,
        enquiry_number=enq_no,
        customer_id=cust_id,
        customer_name=cust_name,
        conducted_by=f.conducted_by,
        conductor_name=conductor_name,
        followup_type=f.followup_type,
        scheduled_at=f.scheduled_at,
        completed_at=f.completed_at,
        status=f.status,
        discussion_summary=f.discussion_summary,
        next_followup_at=f.next_followup_at,
        is_overdue=is_overdue,
        created_at=f.created_at,
    )


@router.get("", response_model=APIResponse[FollowupListResponse])
def list_followups(
    enquiry_id: Optional[int] = Query(None, description="Filter by enquiry ID"),
    conducted_by: Optional[int] = Query(None, description="Filter by employee ID conducting followup"),
    status: Optional[str] = Query(None, description="Filter by status (SCHEDULED, COMPLETED, CANCELLED)"),
    followup_type: Optional[str] = Query(None, description="Filter by type (CALL, EMAIL, VISIT, WHATSAPP)"),
    overdue_only: Optional[bool] = Query(None, description="Filter only overdue followups"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_followup_access),
):
    """
    List follow-up activities.
    Enforces sales data isolation: SALES users only access their own touchpoints.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot access internal follow-up activities",
        )

    stmt = select(Followup).options(
        selectinload(Followup.enquiry).selectinload(Enquiry.customer),
        selectinload(Followup.conductor).selectinload(Employee.user),
    )

    # 1. SALES Data Isolation:
    if current_user.role and current_user.role.slug == SystemRole.SALES:
        emp = _get_employee_for_user(current_user, db)
        if not emp:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sales user is not linked to an active employee record",
            )
        if conducted_by is not None and conducted_by != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sales representatives can only access their own follow-ups",
            )
        # Filter to touchpoints conducted by this employee
        stmt = stmt.where(Followup.conducted_by == emp.id)
    elif conducted_by:
        stmt = stmt.where(Followup.conducted_by == conducted_by)

    if enquiry_id:
        # If SALES, verify enquiry assignment
        if current_user.role and current_user.role.slug == SystemRole.SALES:
            emp = _get_employee_for_user(current_user, db)
            enq = db.execute(select(Enquiry).where(Enquiry.id == enquiry_id)).scalar_one_or_none()
            if enq and enq.assigned_sales_id is not None and enq.assigned_sales_id != emp.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access follow-ups for an enquiry assigned to another representative",
                )
        stmt = stmt.where(Followup.enquiry_id == enquiry_id)

    if status:
        stmt = stmt.where(Followup.status == status.strip().upper())

    if followup_type:
        stmt = stmt.where(Followup.followup_type == followup_type.strip().upper())

    if overdue_only:
        now_utc = datetime.now(timezone.utc)
        stmt = stmt.where(Followup.status == "SCHEDULED", Followup.scheduled_at < now_utc)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar() or 0

    stmt = stmt.order_by(Followup.scheduled_at.desc()).offset((page - 1) * limit).limit(limit)
    followups = db.execute(stmt).scalars().all()

    items = [_build_followup_response(f) for f in followups]
    total_pages = math.ceil(total / limit) if total > 0 else 1

    return APIResponse(
        success=True,
        message="Followups retrieved successfully",
        data=FollowupListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        ),
    )


@router.post("", response_model=APIResponse[FollowupResponse], status_code=status.HTTP_201_CREATED)
def create_followup(
    payload: FollowupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_followup_access),
):
    """
    Schedule a new customer sales follow-up touchpoint.
    Enforces sales data isolation.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot schedule internal follow-ups",
        )

    # Validate enquiry exists
    enquiry = db.execute(
        select(Enquiry).where(Enquiry.id == payload.enquiry_id)
    ).scalar_one_or_none()
    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enquiry with ID {payload.enquiry_id} not found",
        )

    # SALES Isolation: check enquiry assignment
    conductor_id = payload.conducted_by
    if current_user.role and current_user.role.slug == SystemRole.SALES:
        emp = _get_employee_for_user(current_user, db)
        if not emp:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sales user is not linked to an active employee record",
            )
        if enquiry.assigned_sales_id is not None and enquiry.assigned_sales_id != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to schedule follow-ups for an enquiry assigned to another representative",
            )
        if conductor_id is not None and conductor_id != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sales representatives cannot schedule follow-ups for another representative",
            )
        conductor_id = emp.id
    else:
        if conductor_id is None:
            emp = _get_employee_for_user(current_user, db)
            if emp:
                conductor_id = emp.id
            elif enquiry.assigned_sales_id:
                conductor_id = enquiry.assigned_sales_id
            else:
                first_emp = db.execute(select(Employee).where(Employee.is_active == True)).scalars().first()
                if not first_emp:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No employee record available to assign as followup conductor. Specify conducted_by.",
                    )
                conductor_id = first_emp.id
        else:
            emp = db.execute(select(Employee).where(Employee.id == conductor_id)).scalar_one_or_none()
            if not emp:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Employee ID {conductor_id} not found",
                )
            if not emp.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Employee {emp.employee_code} is inactive and cannot conduct follow-ups",
                )

    followup = Followup(
        enquiry_id=payload.enquiry_id,
        conducted_by=conductor_id,
        followup_type=payload.followup_type,
        scheduled_at=payload.scheduled_at,
        status="SCHEDULED",
        discussion_summary=payload.discussion_summary,
        next_followup_at=payload.next_followup_at,
    )
    db.add(followup)

    # Advance NEW enquiry to CONTACTED when scheduling active touchpoint
    if enquiry.status == "NEW":
        enquiry.status = "CONTACTED"
        enquiry.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(followup)

    followup = db.execute(
        select(Followup)
        .where(Followup.id == followup.id)
        .options(
            selectinload(Followup.enquiry).selectinload(Enquiry.customer),
            selectinload(Followup.conductor).selectinload(Employee.user),
        )
    ).scalar_one()

    return APIResponse(
        success=True,
        message="Followup touchpoint scheduled successfully",
        data=_build_followup_response(followup),
    )


@router.put("/{followup_id}/complete", response_model=APIResponse[FollowupResponse])
def complete_followup(
    followup_id: int,
    payload: FollowupComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_followup_access),
):
    """
    Record discussion notes and complete follow-up.
    Enforces sales representative ownership check.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot modify follow-ups",
        )

    followup = db.execute(
        select(Followup)
        .where(Followup.id == followup_id)
        .options(
            selectinload(Followup.enquiry).selectinload(Enquiry.customer),
            selectinload(Followup.conductor).selectinload(Employee.user),
        )
    ).scalar_one_or_none()
    if not followup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Followup with ID {followup_id} not found",
        )

    # SALES Ownership check:
    if current_user.role and current_user.role.slug == SystemRole.SALES:
        emp = _get_employee_for_user(current_user, db)
        if not emp or followup.conducted_by != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to complete another representative's follow-up",
            )

    followup.discussion_summary = payload.discussion_summary.strip()
    followup.completed_at = payload.completed_at or datetime.now(timezone.utc)
    followup.status = payload.status
    if payload.next_followup_at:
        followup.next_followup_at = payload.next_followup_at

    # Optionally transition parent enquiry status
    if payload.update_enquiry_status and followup.enquiry:
        new_status = payload.update_enquiry_status.strip().upper()
        followup.enquiry.status = new_status
        timestamp_prefix = datetime.now().strftime("%Y-%m-%d %H:%M")
        existing_notes = followup.enquiry.notes or ""
        followup.enquiry.notes = f"{existing_notes}\n[{timestamp_prefix} Followup Completed]: {payload.discussion_summary}".strip()
        followup.enquiry.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(followup)

    return APIResponse(
        success=True,
        message="Followup touchpoint completed and recorded",
        data=_build_followup_response(followup),
    )


@router.put("/{followup_id}/reschedule", response_model=APIResponse[FollowupResponse])
def reschedule_followup(
    followup_id: int,
    payload: FollowupReschedule,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_followup_access),
):
    """
    Reschedule an existing scheduled touchpoint to a new datetime.
    Only SCHEDULED follow-ups can be rescheduled. Completed or cancelled follow-ups cannot be rescheduled.
    Preserves reschedule reason in discussion_summary without adding database columns.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot reschedule follow-ups",
        )

    followup = db.execute(
        select(Followup)
        .where(Followup.id == followup_id)
        .options(
            selectinload(Followup.enquiry).selectinload(Enquiry.customer),
            selectinload(Followup.conductor).selectinload(Employee.user),
        )
    ).scalar_one_or_none()
    if not followup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Followup with ID {followup_id} not found",
        )

    # SALES Ownership check:
    if current_user.role and current_user.role.slug == SystemRole.SALES:
        emp = _get_employee_for_user(current_user, db)
        if not emp or followup.conducted_by != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to reschedule another representative's follow-up",
            )

    # State validation: Only SCHEDULED follow-ups can be rescheduled
    if followup.status != "SCHEDULED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reschedule follow-up with status '{followup.status}'. Only SCHEDULED follow-ups may be rescheduled.",
        )

    # Preserve reschedule reason in discussion_summary without schema change
    timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    new_time_str = payload.scheduled_at.strftime("%Y-%m-%d %H:%M")
    reason_note = f"[{timestamp_str} Rescheduled to {new_time_str}]: {payload.reason.strip()}"
    if followup.discussion_summary:
        followup.discussion_summary = f"{followup.discussion_summary}\n{reason_note}".strip()
    else:
        followup.discussion_summary = reason_note

    followup.scheduled_at = payload.scheduled_at
    db.commit()
    db.refresh(followup)

    return APIResponse(
        success=True,
        message="Followup touchpoint rescheduled successfully",
        data=_build_followup_response(followup),
    )
