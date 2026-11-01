from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone, date
import math
import os
import secrets
import hashlib
import re

from app.database import get_db
from app.models.crm import Customer, Enquiry, Survey, SurveyApproval
from app.models.auth import User, Employee, FileAttachment
from app.models.workflow import AuditLog, Notification
from app.schemas.surveys import (
    SurveyScheduleRequest,
    SurveyCreate,
    SurveyUpdate,
    SurveyApprovalCreate,
    SurveyApprovalResponse,
    FileAttachmentResponse,
    SurveyResponse,
    SurveyDetailResponse,
    SurveyListResponse,
    VALID_ROOF_ORIENTATIONS,
    VALID_ROOF_STRUCTURE_TYPES,
    VALID_EXISTING_PHASES,
    VALID_TECHNICAL_FEASIBILITIES,
    VALID_SURVEY_STATUSES,
    VALID_APPROVAL_ACTIONS,
)
from app.schemas import APIResponse
from app.dependencies.auth import get_current_user, require_permissions, get_user_permissions
from app.utils.roles import SystemRole

router = APIRouter(prefix="/surveys", tags=["Site Surveys & Technical Approval"])

UPLOAD_DIR = os.path.join("uploads", "surveys")
ALLOWED_MIME_TYPES = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/webp": [".webp"],
    "application/pdf": [".pdf"],
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


# ==========================================
# INTERNAL HELPERS
# ==========================================

def _get_employee_for_user(user: User, db: Session) -> Optional[Employee]:
    return db.execute(
        select(Employee).where(Employee.user_id == user.id)
    ).scalar_one_or_none()


def _get_customer_for_user(user: User, db: Session) -> Optional[Customer]:
    return db.execute(
        select(Customer).where(Customer.user_id == user.id)
    ).scalar_one_or_none()


def _generate_survey_number(db: Session) -> str:
    """Generate canonical SRV-YYYYMMDD-XXXX candidate."""
    today_str = date.today().strftime("%Y%m%d")
    for _ in range(10):
        suffix = secrets.token_hex(2).upper()
        candidate = f"SRV-{today_str}-{suffix}"
        exists = db.execute(select(Survey.id).where(Survey.survey_number == candidate)).scalar_one_or_none()
        if not exists:
            return candidate
    return f"SRV-{today_str}-{int(datetime.now().timestamp()) % 10000:04d}"


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
        entity_name="SURVEY",
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


def _build_survey_response(s: Survey, db: Session) -> SurveyResponse:
    cust_id = None
    cust_name = None
    cust_phone = None
    cust_city = None
    cust_address = None
    enq_number = None
    proposed_kw = None

    if s.enquiry:
        enq_number = s.enquiry.enquiry_number
        proposed_kw = float(s.enquiry.proposed_capacity_kw) if s.enquiry.proposed_capacity_kw is not None else None
        if s.enquiry.customer:
            cust_id = s.enquiry.customer.id
            cust_name = s.enquiry.customer.full_name
            cust_phone = s.enquiry.customer.phone
            cust_city = s.enquiry.customer.city
            cust_address = s.enquiry.customer.address

    surveyor_code = None
    surveyor_name = None
    if s.surveyor:
        surveyor_code = s.surveyor.employee_code
        if s.surveyor.user:
            surveyor_name = s.surveyor.user.full_name

    # Approvals summary
    approvals_count = len(s.approvals) if s.approvals else 0
    latest_action = None
    latest_comments = None
    if s.approvals:
        sorted_approvals = sorted(s.approvals, key=lambda a: a.revision_number, reverse=True)
        if sorted_approvals:
            latest_action = sorted_approvals[0].action
            latest_comments = sorted_approvals[0].comments

    # Attachments count
    att_count = db.execute(
        select(func.count(FileAttachment.id))
        .where(FileAttachment.entity_type == "SURVEY", FileAttachment.entity_id == s.id)
    ).scalar() or 0

    return SurveyResponse(
        id=s.id,
        enquiry_id=s.enquiry_id,
        enquiry_number=enq_number,
        proposed_capacity_kw=proposed_kw,
        customer_id=cust_id,
        customer_name=cust_name,
        customer_phone=cust_phone,
        customer_city=cust_city,
        customer_address=cust_address,
        surveyor_id=s.surveyor_id,
        surveyor_name=surveyor_name,
        surveyor_code=surveyor_code,
        survey_number=s.survey_number,
        scheduled_at=s.scheduled_at,
        conducted_at=s.conducted_at,
        roof_area_sqft=float(s.roof_area_sqft) if s.roof_area_sqft is not None else None,
        shadow_free_area_sqft=float(s.shadow_free_area_sqft) if s.shadow_free_area_sqft is not None else None,
        roof_orientation=s.roof_orientation,
        roof_tilt_degrees=float(s.roof_tilt_degrees) if s.roof_tilt_degrees is not None else None,
        roof_structure_type=s.roof_structure_type,
        existing_phase=s.existing_phase,
        sanctioned_load_kw=float(s.sanctioned_load_kw) if s.sanctioned_load_kw is not None else None,
        gps_latitude=float(s.gps_latitude) if s.gps_latitude is not None else None,
        gps_longitude=float(s.gps_longitude) if s.gps_longitude is not None else None,
        technical_feasibility=s.technical_feasibility,
        remarks=s.remarks,
        status=s.status,
        approval_count=approvals_count,
        latest_approval_action=latest_action,
        latest_approval_comments=latest_comments,
        attachment_count=att_count,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


def _build_survey_detail_response(s: Survey, db: Session) -> SurveyDetailResponse:
    base = _build_survey_response(s, db)

    # Approvals list
    approval_items = []
    if s.approvals:
        sorted_approvals = sorted(s.approvals, key=lambda a: a.revision_number)
        for a in sorted_approvals:
            rev_name = a.reviewer.full_name if a.reviewer else None
            rev_role = a.reviewer.role.name if a.reviewer and a.reviewer.role else None
            approval_items.append(
                SurveyApprovalResponse(
                    id=a.id,
                    survey_id=a.survey_id,
                    reviewer_id=a.reviewer_id,
                    reviewer_name=rev_name,
                    reviewer_role=rev_role,
                    action=a.action,
                    comments=a.comments,
                    revision_number=a.revision_number,
                    reviewed_at=a.reviewed_at,
                    created_at=a.created_at,
                )
            )

    # Attachments list
    attachments = db.execute(
        select(FileAttachment)
        .where(FileAttachment.entity_type == "SURVEY", FileAttachment.entity_id == s.id)
        .options(selectinload(FileAttachment.uploader))
        .order_by(FileAttachment.created_at.desc())
    ).scalars().all()

    attachment_items = [
        FileAttachmentResponse(
            id=att.id,
            entity_type=att.entity_type,
            entity_id=att.entity_id,
            file_name=att.file_name,
            file_size_bytes=att.file_size_bytes,
            mime_type=att.mime_type,
            storage_backend=att.storage_backend,
            uploaded_by=att.uploaded_by,
            uploader_name=att.uploader.full_name if att.uploader else None,
            created_at=att.created_at,
        )
        for att in attachments
    ]

    return SurveyDetailResponse(
        **base.model_dump(),
        approvals=approval_items,
        attachments=attachment_items,
    )


# ==========================================
# ENDPOINTS
# ==========================================

@router.post("", response_model=APIResponse[SurveyResponse], status_code=status.HTTP_201_CREATED)
def schedule_survey(
    payload: SurveyScheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Schedule a new site survey for a qualified CRM enquiry.
    Authorized roles: SALES (own assigned enquiries only), TECHNICAL_MANAGER, DIRECTOR, SUPER_ADMIN.
    Rejects CUSTOMER and FIELD_TECHNICIAN.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot schedule site surveys",
        )

    if current_user.role and current_user.role.slug == SystemRole.FIELD_TECHNICIAN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Field technicians cannot schedule or assign site surveys",
        )

    # Validate Enquiry
    enquiry = db.execute(
        select(Enquiry)
        .where(Enquiry.id == payload.enquiry_id)
        .options(selectinload(Enquiry.customer))
    ).scalar_one_or_none()
    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enquiry with ID {payload.enquiry_id} not found",
        )

    if enquiry.status in ("CANCELLED", "LOST"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot schedule survey for an enquiry with status '{enquiry.status}'",
        )

    # SALES Ownership Check
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
                detail="Sales representatives can only schedule surveys for their own assigned enquiries",
            )
        # If enquiry was unassigned, claim it for this representative
        if enquiry.assigned_sales_id is None:
            enquiry.assigned_sales_id = emp.id

    # Validate Surveyor Employee
    surveyor = db.execute(
        select(Employee)
        .where(Employee.id == payload.surveyor_id)
        .options(selectinload(Employee.user))
    ).scalar_one_or_none()
    if not surveyor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Surveyor employee with ID {payload.surveyor_id} not found",
        )
    if not surveyor.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee {surveyor.employee_code} is inactive and cannot be assigned surveys",
        )

    # Check for duplicate active survey on this enquiry
    existing_active = db.execute(
        select(Survey).where(
            Survey.enquiry_id == enquiry.id,
            Survey.status.in_(("DRAFT", "SUBMITTED", "UNDER_REVIEW", "CORRECTION_REQUESTED", "APPROVED")),
        )
    ).first()
    if existing_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An active or approved survey already exists for Enquiry ID {enquiry.id}",
        )

    # Concurrency-safe creation with retry on duplicate survey_number conflict
    max_retries = 3
    survey = None
    for attempt in range(max_retries):
        srv_number = _generate_survey_number(db)
        survey = Survey(
            enquiry_id=payload.enquiry_id,
            surveyor_id=payload.surveyor_id,
            survey_number=srv_number,
            scheduled_at=payload.scheduled_at,
            status="DRAFT",
            remarks=payload.remarks,
        )
        db.add(survey)
        try:
            db.commit()
            db.refresh(survey)
            break
        except IntegrityError as exc:
            db.rollback()
            err_str = str(exc).lower()
            if "survey_number" in err_str or "ix_surveys_survey_number" in err_str or "unique" in err_str:
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Unable to generate a unique survey number after multiple attempts. Please retry.",
                    )
                continue
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database integrity conflict during survey scheduling: {str(exc.orig) if hasattr(exc, 'orig') else str(exc)}",
            )

    # Advance enquiry status to SURVEY_REQUESTED if newly scheduled
    if enquiry.status in ("NEW", "CONTACTED"):
        enquiry.status = "SURVEY_REQUESTED"
        enquiry.updated_at = datetime.now(timezone.utc)
        db.commit()

    # Audit & Notification
    _record_audit_log(
        db,
        user_id=current_user.id,
        action="CREATE",
        entity_id=survey.id,
        details={"survey_number": survey.survey_number, "enquiry_id": enquiry.id, "surveyor_id": surveyor.id},
    )
    if surveyor.user_id:
        _send_notification(
            db,
            user_id=surveyor.user_id,
            title="New Site Survey Assigned",
            message=f"You have been assigned to conduct survey {survey.survey_number} for Enquiry {enquiry.enquiry_number}.",
            notification_type="TASK",
            link_url=f"/surveys/{survey.id}",
        )
    db.commit()

    # Eager reload
    survey = db.execute(
        select(Survey)
        .where(Survey.id == survey.id)
        .options(
            selectinload(Survey.enquiry).selectinload(Enquiry.customer),
            selectinload(Survey.surveyor).selectinload(Employee.user),
            selectinload(Survey.approvals),
        )
    ).scalar_one()

    return APIResponse(
        success=True,
        message="Site survey scheduled successfully",
        data=_build_survey_response(survey, db),
    )


@router.get("", response_model=APIResponse[SurveyListResponse])
def list_surveys(
    survey_status: Optional[str] = Query(None, alias="status", description="Filter by status (DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, CORRECTION_REQUESTED)"),
    surveyor_id: Optional[int] = Query(None, description="Filter by assigned surveyor employee ID"),
    enquiry_id: Optional[int] = Query(None, description="Filter by enquiry ID"),
    search: Optional[str] = Query(None, description="Search by survey number, customer name, phone, or city"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List site surveys with role-based data isolation.
    - FIELD_TECHNICIAN sees only their assigned surveys.
    - SALES sees only surveys linked to enquiries within their assignment scope.
    - TECHNICAL_MANAGER, DIRECTOR, SUPER_ADMIN see all surveys.
    - CUSTOMER sees only surveys linked to their own customer account.
    """
    stmt = (
        select(Survey)
        .join(Survey.enquiry)
        .join(Enquiry.customer)
        .options(
            selectinload(Survey.enquiry).selectinload(Enquiry.customer),
            selectinload(Survey.surveyor).selectinload(Employee.user),
            selectinload(Survey.approvals),
        )
    )

    # Customer Data Scoping
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        cust = _get_customer_for_user(current_user, db)
        if not cust:
            return APIResponse(
                success=True,
                message="No site surveys found",
                data=SurveyListResponse(items=[], total=0, page=page, limit=limit, total_pages=0),
            )
        stmt = stmt.where(Enquiry.customer_id == cust.id)

    # 1. FIELD_TECHNICIAN Isolation
    if current_user.role and current_user.role.slug == SystemRole.FIELD_TECHNICIAN:
        emp = _get_employee_for_user(current_user, db)
        if not emp:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Field technician is not linked to an active employee record",
            )
        if surveyor_id is not None and surveyor_id != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Field technicians can only view their own assigned surveys",
            )
        stmt = stmt.where(Survey.surveyor_id == emp.id)
    elif surveyor_id:
        stmt = stmt.where(Survey.surveyor_id == surveyor_id)

    # 2. SALES Isolation
    if current_user.role and current_user.role.slug == SystemRole.SALES:
        emp = _get_employee_for_user(current_user, db)
        if not emp:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sales user is not linked to an active employee record",
            )
        if enquiry_id is not None:
            target_enq = db.execute(select(Enquiry).where(Enquiry.id == enquiry_id)).scalar_one_or_none()
            if target_enq and target_enq.assigned_sales_id is not None and target_enq.assigned_sales_id != emp.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access surveys for an enquiry assigned to another sales representative",
                )
        stmt = stmt.where(
            or_(
                Enquiry.assigned_sales_id == emp.id,
                Enquiry.assigned_sales_id.is_(None),
            )
        )

    if enquiry_id:
        stmt = stmt.where(Survey.enquiry_id == enquiry_id)

    if survey_status:
        clean_status = survey_status.strip().upper()
        if clean_status in VALID_SURVEY_STATUSES:
            stmt = stmt.where(Survey.status == clean_status)

    if search:
        term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Survey.survey_number).like(term),
                func.lower(Customer.full_name).like(term),
                func.lower(Customer.phone).like(term),
                func.lower(Customer.city).like(term),
            )
        )

    # Total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar() or 0

    stmt = stmt.order_by(Survey.scheduled_at.desc()).offset((page - 1) * limit).limit(limit)
    surveys = db.execute(stmt).scalars().all()

    items = [_build_survey_response(s, db) for s in surveys]
    total_pages = math.ceil(total / limit) if total > 0 else 1

    return APIResponse(
        success=True,
        message="Surveys retrieved successfully",
        data=SurveyListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        ),
    )


@router.get("/{survey_id}", response_model=APIResponse[SurveyDetailResponse])
def get_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve full survey details including technical specs, review history, and attachments.
    Enforces role data isolation.
    """
    survey = db.execute(
        select(Survey)
        .where(Survey.id == survey_id)
        .options(
            selectinload(Survey.enquiry).selectinload(Enquiry.customer),
            selectinload(Survey.surveyor).selectinload(Employee.user),
            selectinload(Survey.approvals).selectinload(SurveyApproval.reviewer).selectinload(User.role),
        )
    ).scalar_one_or_none()
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Survey with ID {survey_id} not found",
        )

    # Scoping checks
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        cust = _get_customer_for_user(current_user, db)
        if not cust or (survey.enquiry and survey.enquiry.customer_id != cust.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access site surveys associated with your own customer account",
            )
    if current_user.role and current_user.role.slug == SystemRole.FIELD_TECHNICIAN:
        emp = _get_employee_for_user(current_user, db)
        if not emp or survey.surveyor_id != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view surveys assigned to another technician",
            )
    elif current_user.role and current_user.role.slug == SystemRole.SALES:
        emp = _get_employee_for_user(current_user, db)
        if not emp or (survey.enquiry.assigned_sales_id is not None and survey.enquiry.assigned_sales_id != emp.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view surveys for another sales representative's enquiry",
            )

    return APIResponse(
        success=True,
        message="Survey details retrieved successfully",
        data=_build_survey_detail_response(survey, db),
    )


@router.put("/{survey_id}", response_model=APIResponse[SurveyResponse])
def update_survey_observations(
    survey_id: int,
    payload: SurveyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update site survey measurements, orientation, structural, and electrical observations.
    Only DRAFT and CORRECTION_REQUESTED surveys can be modified.
    Only assigned surveyor or authorized executive/manager can update.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot modify site surveys",
        )

    survey = db.execute(
        select(Survey)
        .where(Survey.id == survey_id)
        .options(
            selectinload(Survey.enquiry).selectinload(Enquiry.customer),
            selectinload(Survey.surveyor).selectinload(Employee.user),
            selectinload(Survey.approvals),
        )
    ).scalar_one_or_none()
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Survey with ID {survey_id} not found",
        )

    # State validation: Approved or Rejected surveys cannot be modified
    if survey.status not in ("DRAFT", "CORRECTION_REQUESTED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot edit survey with status '{survey.status}'. Only DRAFT or CORRECTION_REQUESTED surveys can be modified.",
        )

    # Authorization validation:
    if current_user.role and current_user.role.slug == SystemRole.FIELD_TECHNICIAN:
        emp = _get_employee_for_user(current_user, db)
        if not emp or survey.surveyor_id != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update another technician's assigned survey",
            )
    elif current_user.role and current_user.role.slug == SystemRole.SALES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sales representatives cannot record or edit technical survey observations",
        )

    # Physical Area Validation
    effective_roof = float(payload.roof_area_sqft) if payload.roof_area_sqft is not None else (float(survey.roof_area_sqft) if survey.roof_area_sqft is not None else None)
    effective_shadow = float(payload.shadow_free_area_sqft) if payload.shadow_free_area_sqft is not None else (float(survey.shadow_free_area_sqft) if survey.shadow_free_area_sqft is not None else None)

    if effective_roof is not None and effective_shadow is not None:
        if effective_shadow > effective_roof:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Shadow-free area ({effective_shadow} sqft) cannot exceed total roof area ({effective_roof} sqft)",
            )

    # Apply updates
    if payload.scheduled_at is not None:
        survey.scheduled_at = payload.scheduled_at
    if payload.conducted_at is not None:
        survey.conducted_at = payload.conducted_at
    if payload.roof_area_sqft is not None:
        survey.roof_area_sqft = payload.roof_area_sqft
    if payload.shadow_free_area_sqft is not None:
        survey.shadow_free_area_sqft = payload.shadow_free_area_sqft
    if payload.roof_orientation is not None:
        survey.roof_orientation = payload.roof_orientation
    if payload.roof_tilt_degrees is not None:
        survey.roof_tilt_degrees = payload.roof_tilt_degrees
    if payload.roof_structure_type is not None:
        survey.roof_structure_type = payload.roof_structure_type
    if payload.existing_phase is not None:
        survey.existing_phase = payload.existing_phase
    if payload.sanctioned_load_kw is not None:
        survey.sanctioned_load_kw = payload.sanctioned_load_kw
    if payload.gps_latitude is not None:
        survey.gps_latitude = payload.gps_latitude
    if payload.gps_longitude is not None:
        survey.gps_longitude = payload.gps_longitude
    if payload.technical_feasibility is not None:
        survey.technical_feasibility = payload.technical_feasibility
    if payload.remarks is not None:
        survey.remarks = payload.remarks

    survey.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(survey)

    _record_audit_log(
        db,
        user_id=current_user.id,
        action="UPDATE",
        entity_id=survey.id,
        details={"status": survey.status},
    )
    db.commit()

    return APIResponse(
        success=True,
        message="Survey observations updated successfully",
        data=_build_survey_response(survey, db),
    )


@router.put("/{survey_id}/submit", response_model=APIResponse[SurveyResponse])
def submit_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit completed site survey for technical review.
    Only DRAFT or CORRECTION_REQUESTED surveys can be submitted.
    Enforces minimum required survey observations.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot submit site surveys",
        )

    survey = db.execute(
        select(Survey)
        .where(Survey.id == survey_id)
        .options(
            selectinload(Survey.enquiry).selectinload(Enquiry.customer),
            selectinload(Survey.surveyor).selectinload(Employee.user),
            selectinload(Survey.approvals),
        )
    ).scalar_one_or_none()
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Survey with ID {survey_id} not found",
        )

    if survey.status not in ("DRAFT", "CORRECTION_REQUESTED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit survey with status '{survey.status}'. Only DRAFT or CORRECTION_REQUESTED surveys can be submitted.",
        )

    # Authorization
    if current_user.role and current_user.role.slug == SystemRole.FIELD_TECHNICIAN:
        emp = _get_employee_for_user(current_user, db)
        if not emp or survey.surveyor_id != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the assigned surveyor can submit this survey",
            )
    elif current_user.role and current_user.role.slug not in (SystemRole.SUPER_ADMIN, SystemRole.TECHNICAL_MANAGER, SystemRole.DIRECTOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges to submit site survey",
        )

    # Validation: minimum required survey observations based on schema
    missing_fields = []
    if survey.roof_area_sqft is None or float(survey.roof_area_sqft) <= 0:
        missing_fields.append("roof_area_sqft (> 0)")
    if survey.shadow_free_area_sqft is None or float(survey.shadow_free_area_sqft) < 0:
        missing_fields.append("shadow_free_area_sqft (>= 0)")
    if survey.roof_orientation is None:
        missing_fields.append("roof_orientation")
    if survey.existing_phase is None:
        missing_fields.append("existing_phase")
    if survey.technical_feasibility is None:
        missing_fields.append("technical_feasibility")

    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit survey: missing required technical observations: {', '.join(missing_fields)}",
        )

    # Transition state to SUBMITTED
    survey.status = "SUBMITTED"
    if survey.conducted_at is None:
        survey.conducted_at = datetime.now(timezone.utc)
    survey.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(survey)

    _record_audit_log(
        db,
        user_id=current_user.id,
        action="SUBMIT",
        entity_id=survey.id,
        details={"survey_number": survey.survey_number},
    )
    db.commit()

    return APIResponse(
        success=True,
        message=f"Survey {survey.survey_number} submitted for technical review",
        data=_build_survey_response(survey, db),
    )


@router.post("/{survey_id}/review", response_model=APIResponse[SurveyDetailResponse])
def review_survey(
    survey_id: int,
    payload: SurveyApprovalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Technical review decision for a submitted site survey.
    Allowed actions: APPROVED, REJECTED, CORRECTION_REQUESTED.
    Authorized reviewers: TECHNICAL_MANAGER, DIRECTOR, SUPER_ADMIN.
    Requires survey status to be SUBMITTED or UNDER_REVIEW.
    Appends review history in survey_approvals table.
    """
    # Enforce Reviewer Role
    user_role_slug = current_user.role.slug if current_user.role else ""
    if user_role_slug not in (SystemRole.SUPER_ADMIN, SystemRole.TECHNICAL_MANAGER, SystemRole.DIRECTOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Technical Managers, Directors, or Super Admins can make technical approval decisions",
        )

    survey = db.execute(
        select(Survey)
        .where(Survey.id == survey_id)
        .options(
            selectinload(Survey.enquiry).selectinload(Enquiry.customer),
            selectinload(Survey.surveyor).selectinload(Employee.user),
            selectinload(Survey.approvals).selectinload(SurveyApproval.reviewer).selectinload(User.role),
        )
    ).scalar_one_or_none()
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Survey with ID {survey_id} not found",
        )

    # State validation: DRAFT surveys cannot be reviewed directly
    if survey.status == "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot review survey with status 'DRAFT'. Survey must be submitted by surveyor before technical review.",
        )

    if survey.status in ("APPROVED", "REJECTED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Survey {survey.survey_number} has already been finalized with status '{survey.status}' and cannot be reviewed again.",
        )

    action = payload.action.strip().upper()
    comments = payload.comments.strip()

    if action in ("REJECTED", "CORRECTION_REQUESTED") and len(comments) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Detailed comments (at least 5 characters) are required for decision '{action}'",
        )

    # Increment revision number
    existing_revisions = len(survey.approvals) if survey.approvals else 0
    next_revision = existing_revisions + 1

    approval = SurveyApproval(
        survey_id=survey.id,
        reviewer_id=current_user.id,
        action=action,
        comments=comments,
        revision_number=next_revision,
        reviewed_at=datetime.now(timezone.utc),
    )
    db.add(approval)

    # Update Survey Status
    survey.status = action
    survey.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(survey)

    # Note: Enquiry status remains SURVEY_REQUESTED as per approved business rule.
    # Audit & Notification
    _record_audit_log(
        db,
        user_id=current_user.id,
        action=action,
        entity_id=survey.id,
        details={"survey_number": survey.survey_number, "action": action, "revision_number": next_revision},
    )

    if survey.surveyor and survey.surveyor.user_id:
        _send_notification(
            db,
            user_id=survey.surveyor.user_id,
            title=f"Survey {survey.survey_number} Review: {action}",
            message=f"Review decision: {action}. Reviewer comments: {comments}",
            notification_type="APPROVAL",
            link_url=f"/surveys/{survey.id}",
        )
    db.commit()

    # Reload survey for full response
    survey = db.execute(
        select(Survey)
        .where(Survey.id == survey.id)
        .options(
            selectinload(Survey.enquiry).selectinload(Enquiry.customer),
            selectinload(Survey.surveyor).selectinload(Employee.user),
            selectinload(Survey.approvals).selectinload(SurveyApproval.reviewer).selectinload(User.role),
        )
    ).scalar_one()

    return APIResponse(
        success=True,
        message=f"Technical review recorded: Survey is now {action}",
        data=_build_survey_detail_response(survey, db),
    )


@router.post("/{survey_id}/attachments", response_model=APIResponse[FileAttachmentResponse], status_code=status.HTTP_201_CREATED)
async def upload_survey_attachment(
    survey_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload site photos, shadow layout drawings, or technical survey documents.
    Validates file format (JPEG, PNG, WEBP, PDF) and file size (<= 10MB).
    Restricted to authorized users for this survey.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot upload survey attachments",
        )

    survey = db.execute(
        select(Survey)
        .where(Survey.id == survey_id)
        .options(
            selectinload(Survey.enquiry),
            selectinload(Survey.surveyor),
        )
    ).scalar_one_or_none()
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Survey with ID {survey_id} not found",
        )

    # Scoping check
    if current_user.role and current_user.role.slug == SystemRole.FIELD_TECHNICIAN:
        emp = _get_employee_for_user(current_user, db)
        if not emp or survey.surveyor_id != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to attach files to another technician's survey",
            )
    elif current_user.role and current_user.role.slug == SystemRole.SALES:
        emp = _get_employee_for_user(current_user, db)
        if not emp or (survey.enquiry.assigned_sales_id is not None and survey.enquiry.assigned_sales_id != emp.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to attach files to another sales representative's survey",
            )

    # Completed or rejected surveys cannot have attachments added
    if survey.status in ("APPROVED", "REJECTED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot add attachments to finalized survey with status '{survey.status}'",
        )

    # File format validation
    content_type = file.content_type or ""
    orig_filename = os.path.basename(file.filename or "attachment")
    ext = os.path.splitext(orig_filename)[1].lower()

    valid_type = False
    for mime, exts in ALLOWED_MIME_TYPES.items():
        if content_type == mime or ext in exts:
            valid_type = True
            break

    if not valid_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed formats: JPEG, PNG, WEBP, PDF. Detected: {content_type or ext}",
        )

    # Read and validate file size
    contents = await file.read()
    file_size = len(contents)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds 10MB limit ({file_size / (1024*1024):.2f}MB)",
        )

    # Compute SHA256
    sha256_hash = hashlib.sha256(contents).hexdigest()

    # Save to disk
    target_dir = os.path.join(UPLOAD_DIR, str(survey.id))
    os.makedirs(target_dir, exist_ok=True)
    sanitized_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", orig_filename)
    unique_filename = f"{secrets.token_hex(4)}_{sanitized_name}"
    full_path = os.path.join(target_dir, unique_filename)

    with open(full_path, "wb") as f_out:
        f_out.write(contents)

    # Record in file_attachments
    attachment = FileAttachment(
        entity_type="SURVEY",
        entity_id=survey.id,
        file_name=orig_filename,
        file_path=full_path.replace("\\", "/"),
        file_size_bytes=file_size,
        mime_type=content_type or "application/octet-stream",
        storage_backend="LOCAL",
        checksum_sha256=sha256_hash,
        uploaded_by=current_user.id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    _record_audit_log(
        db,
        user_id=current_user.id,
        action="ATTACHMENT_UPLOAD",
        entity_id=survey.id,
        details={"file_name": orig_filename, "file_size": file_size},
    )
    db.commit()

    return APIResponse(
        success=True,
        message="Survey attachment uploaded successfully",
        data=FileAttachmentResponse(
            id=attachment.id,
            entity_type=attachment.entity_type,
            entity_id=attachment.entity_id,
            file_name=attachment.file_name,
            file_size_bytes=attachment.file_size_bytes,
            mime_type=attachment.mime_type,
            storage_backend=attachment.storage_backend,
            uploaded_by=attachment.uploaded_by,
            uploader_name=current_user.full_name,
            created_at=attachment.created_at,
        ),
    )


@router.get("/{survey_id}/attachments", response_model=APIResponse[List[FileAttachmentResponse]])
def list_survey_attachments(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all uploaded site photographs and supporting documents for a survey.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot access internal survey attachments",
        )

    survey = db.execute(
        select(Survey)
        .where(Survey.id == survey_id)
        .options(
            selectinload(Survey.enquiry),
            selectinload(Survey.surveyor),
        )
    ).scalar_one_or_none()
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Survey with ID {survey_id} not found",
        )

    # Scoping check
    if current_user.role and current_user.role.slug == SystemRole.FIELD_TECHNICIAN:
        emp = _get_employee_for_user(current_user, db)
        if not emp or survey.surveyor_id != emp.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access another technician's survey attachments",
            )
    elif current_user.role and current_user.role.slug == SystemRole.SALES:
        emp = _get_employee_for_user(current_user, db)
        if not emp or (survey.enquiry.assigned_sales_id is not None and survey.enquiry.assigned_sales_id != emp.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access another sales representative's survey attachments",
            )

    attachments = db.execute(
        select(FileAttachment)
        .where(FileAttachment.entity_type == "SURVEY", FileAttachment.entity_id == survey.id)
        .options(selectinload(FileAttachment.uploader))
        .order_by(FileAttachment.created_at.desc())
    ).scalars().all()

    items = [
        FileAttachmentResponse(
            id=att.id,
            entity_type=att.entity_type,
            entity_id=att.entity_id,
            file_name=att.file_name,
            file_size_bytes=att.file_size_bytes,
            mime_type=att.mime_type,
            storage_backend=att.storage_backend,
            uploaded_by=att.uploaded_by,
            uploader_name=att.uploader.full_name if att.uploader else None,
            created_at=att.created_at,
        )
        for att in attachments
    ]

    return APIResponse(
        success=True,
        message="Survey attachments retrieved successfully",
        data=items,
    )
