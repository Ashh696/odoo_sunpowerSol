from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, and_
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models.crm import Customer, Enquiry, Followup
from app.models.auth import User, Employee
from app.schemas.crm import (
    CRMDashboardMetrics,
    EnquiryResponse,
    FollowupResponse,
)
from app.schemas import APIResponse
from app.dependencies.auth import get_current_user, require_permissions
from app.utils.roles import SystemRole
from app.routers.enquiries import _build_enquiry_response
from app.routers.followups import _build_followup_response

router = APIRouter(prefix="/crm", tags=["CRM Analytics & Dashboard"])


@router.get("/dashboard", response_model=APIResponse[CRMDashboardMetrics])
def get_crm_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("enquiries.read")),
):
    """
    Consolidated CRM sales pipeline and follow-up metrics.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot access internal CRM analytics",
        )

    # 1. Customer metrics
    total_customers = db.execute(select(func.count(Customer.id))).scalar() or 0
    active_customers = db.execute(
        select(func.count(Customer.id)).where(Customer.is_active == True)
    ).scalar() or 0

    # 2. Enquiry metrics
    total_enquiries = db.execute(select(func.count(Enquiry.id))).scalar() or 0

    # Enquiries grouped by status
    status_rows = db.execute(
        select(Enquiry.status, func.count(Enquiry.id)).group_by(Enquiry.status)
    ).all()
    enquiries_by_status = {row[0]: row[1] for row in status_rows}

    # Ensure canonical statuses are present with 0 if no records
    canonical_statuses = ["NEW", "CONTACTED", "SURVEY_REQUESTED", "QUOTED", "WON", "LOST", "CANCELLED"]
    for s in canonical_statuses:
        if s not in enquiries_by_status:
            enquiries_by_status[s] = 0

    # Enquiries grouped by source
    source_rows = db.execute(
        select(Enquiry.source, func.count(Enquiry.id)).group_by(Enquiry.source)
    ).all()
    enquiries_by_source = {row[0]: row[1] for row in source_rows}

    # Enquiries grouped by system type
    sys_rows = db.execute(
        select(Enquiry.system_type, func.count(Enquiry.id)).group_by(Enquiry.system_type)
    ).all()
    enquiries_by_system_type = {row[0]: row[1] for row in sys_rows}

    # 3. Followup metrics
    now_utc = datetime.now(timezone.utc)
    today_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    overdue_count = db.execute(
        select(func.count(Followup.id)).where(
            Followup.status == "SCHEDULED",
            Followup.scheduled_at < now_utc,
        )
    ).scalar() or 0

    today_count = db.execute(
        select(func.count(Followup.id)).where(
            Followup.status == "SCHEDULED",
            Followup.scheduled_at >= today_start,
            Followup.scheduled_at < today_end,
        )
    ).scalar() or 0

    # Conversion rate: WON / total enquiries * 100
    won_count = enquiries_by_status.get("WON", 0)
    conversion_rate = round((won_count / total_enquiries * 100), 1) if total_enquiries > 0 else 0.0

    # Recent enquiries (up to 5)
    recent_enquiries_stmt = (
        select(Enquiry)
        .options(
            selectinload(Enquiry.customer),
            selectinload(Enquiry.assigned_sales).selectinload(Employee.user),
        )
        .order_by(Enquiry.created_at.desc())
        .limit(5)
    )
    recent_enquiries = db.execute(recent_enquiries_stmt).scalars().all()
    recent_enq_items = [_build_enquiry_response(e, db) for e in recent_enquiries]

    # Upcoming / pending followups (up to 5)
    pending_followups_stmt = (
        select(Followup)
        .where(Followup.status == "SCHEDULED")
        .options(
            selectinload(Followup.enquiry).selectinload(Enquiry.customer),
            selectinload(Followup.conductor).selectinload(Employee.user),
        )
        .order_by(Followup.scheduled_at.asc())
        .limit(5)
    )
    pending_followups = db.execute(pending_followups_stmt).scalars().all()
    pending_followup_items = [_build_followup_response(f) for f in pending_followups]

    return APIResponse(
        success=True,
        message="CRM dashboard metrics retrieved successfully",
        data=CRMDashboardMetrics(
            total_customers=total_customers,
            active_customers=active_customers,
            total_enquiries=total_enquiries,
            enquiries_by_status=enquiries_by_status,
            enquiries_by_source=enquiries_by_source,
            enquiries_by_system_type=enquiries_by_system_type,
            overdue_followups_count=overdue_count,
            scheduled_today_followups_count=today_count,
            conversion_rate_percentage=conversion_rate,
            recent_enquiries=recent_enq_items,
            pending_followups=pending_followup_items,
        ),
    )
