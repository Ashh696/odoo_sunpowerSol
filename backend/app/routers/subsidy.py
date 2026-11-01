from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_, desc
from datetime import datetime, date, timezone
from decimal import Decimal
import math

from app.database import get_db
from app.models.auth import User, Role, FileAttachment
from app.models.workflow import AuditLog
from app.models.crm import Customer
from app.models.projects import Project
from app.models.subsidy import (
    SubsidyApplication,
    SubsidyDocument,
    SubsidyStatusHistory,
    SubsidyPayment,
)
from app.schemas.subsidy import (
    SubsidyApplicationCreate,
    SubsidyApplicationUpdate,
    SubsidyStatusTransitionRequest,
    SubsidyDocumentUploadRequest,
    SubsidyDocumentVerificationRequest,
    SubsidyDocumentResponse,
    SubsidyStatusHistoryResponse,
    SubsidyPaymentCreate,
    SubsidyPaymentResponse,
    SubsidyApplicationResponse,
    SubsidyApplicationDetailResponse,
    VALID_SUBSIDY_STATUSES,
    VALID_SUBSIDY_DOC_TYPES,
    VALID_DOC_VERIFICATION_STATUSES,
)
from app.schemas import APIResponse
from app.dependencies.auth import get_current_user
from app.utils.roles import SystemRole

router = APIRouter(tags=["Subsidy Management & DISCOM Liaison"])


# ==========================================
# INTERNAL HELPERS & AUTHORIZATION
# ==========================================

def _calculate_standard_subsidy(capacity_kw: Decimal) -> Decimal:
    """
    PM Surya Ghar standard-state solar rooftop subsidy slabs:
    - Capacity <= 0 kW: ₹0.00
    - Capacity up to and including 2 kW: ₹30,000 per kW (pro-rata)
    - Capacity above 2 kW and below 3 kW: ₹60,000 + ₹18,000 per additional kW (pro-rata)
    - Capacity at or above 3 kW: ₹78,000 (standard-state maximum cap)
    Note: Standard-state rates apply. Special-category states/UTs (NE, UK, HP, J&K, Ladakh,
    Lakshadweep, A&N) and state-specific top-ups are not covered by this standard calculation.
    """
    if capacity_kw <= Decimal("0"):
        return Decimal("0.00")
    elif capacity_kw <= Decimal("2.0"):
        return (capacity_kw * Decimal("30000.00")).quantize(Decimal("0.01"))
    elif capacity_kw < Decimal("3.0"):
        additional_kw = capacity_kw - Decimal("2.0")
        sub = Decimal("60000.00") + (additional_kw * Decimal("18000.00"))
        return sub.quantize(Decimal("0.01"))
    else:
        return Decimal("78000.00")


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


def require_subsidy_read(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role and current_user.role.slug in {
        SystemRole.SUPER_ADMIN,
        SystemRole.DIRECTOR,
        SystemRole.TECHNICAL_MANAGER,
        SystemRole.SERVICE_WARRANTY,
        SystemRole.SALES,
        SystemRole.FINANCE_ACCOUNTS,
        SystemRole.CUSTOMER,
    }:
        return current_user
    raise HTTPException(status_code=403, detail="Unauthorized to view subsidy information")


def require_subsidy_manager(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role and current_user.role.slug in {
        SystemRole.SUPER_ADMIN,
        SystemRole.DIRECTOR,
        SystemRole.TECHNICAL_MANAGER,
        SystemRole.SERVICE_WARRANTY,
    }:
        return current_user
    raise HTTPException(status_code=403, detail="Subsidy & DISCOM officer authorization required")


def _generate_application_number(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"SUB-{year}-"
    latest = (
        db.execute(
            select(SubsidyApplication.application_number)
            .where(SubsidyApplication.application_number.like(f"{prefix}%"))
            .order_by(SubsidyApplication.application_number.desc())
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


def _generate_subsidy_payment_ref(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"SUBPAY-{year}-"
    latest = (
        db.execute(
            select(SubsidyPayment.payment_reference)
            .where(SubsidyPayment.payment_reference.like(f"{prefix}%"))
            .order_by(SubsidyPayment.payment_reference.desc())
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
# 1. SUBSIDY APPLICATIONS
# ==========================================

@router.get("/subsidy/applications", response_model=APIResponse[dict])
def list_subsidy_applications(
    project_id: Optional[int] = Query(None),
    customer_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_subsidy_read),
    db: Session = Depends(get_db),
):
    query = (
        select(SubsidyApplication)
        .options(
            selectinload(SubsidyApplication.project),
            selectinload(SubsidyApplication.customer),
            selectinload(SubsidyApplication.creator),
        )
    )

    # Customer isolation
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        cust = db.execute(select(Customer).where(Customer.user_id == current_user.id)).scalar_one_or_none()
        if not cust:
            return APIResponse(message="No subsidy applications found", data={"items": [], "total": 0, "page": 1, "page_size": page_size, "total_pages": 0})
        query = query.where(SubsidyApplication.customer_id == cust.id)
    else:
        if customer_id:
            query = query.where(SubsidyApplication.customer_id == customer_id)

    if project_id:
        query = query.where(SubsidyApplication.project_id == project_id)
    if status_filter:
        query = query.where(SubsidyApplication.status == status_filter.strip().upper())
    if search:
        s = f"%{search.strip()}%"
        query = query.where(
            or_(
                SubsidyApplication.application_number.ilike(s),
                SubsidyApplication.portal_registration_number.ilike(s),
                SubsidyApplication.discom_name.ilike(s),
            )
        )

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0

    apps = (
        db.execute(
            query.order_by(SubsidyApplication.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    items = [
        SubsidyApplicationResponse(
            id=a.id,
            application_number=a.application_number,
            project_id=a.project_id,
            project_code=a.project.project_code if a.project else None,
            customer_id=a.customer_id,
            customer_name=a.customer.full_name if a.customer else None,
            customer_phone=a.customer.phone if a.customer else None,
            portal_registration_number=a.portal_registration_number,
            discom_name=a.discom_name,
            sanctioned_capacity_kw=a.sanctioned_capacity_kw,
            eligible_subsidy_amount=a.eligible_subsidy_amount,
            application_date=a.application_date,
            status=a.status,
            rejection_reason=a.rejection_reason,
            created_by=a.created_by,
            creator_name=a.creator.full_name if a.creator else None,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in apps
    ]

    return APIResponse(
        message="Subsidy applications retrieved",
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        },
    )


@router.get("/subsidy/applications/{id}", response_model=APIResponse[SubsidyApplicationDetailResponse])
def get_subsidy_application(
    id: int,
    current_user: User = Depends(require_subsidy_read),
    db: Session = Depends(get_db),
):
    app = (
        db.execute(
            select(SubsidyApplication)
            .options(
                selectinload(SubsidyApplication.project),
                selectinload(SubsidyApplication.customer),
                selectinload(SubsidyApplication.creator),
                selectinload(SubsidyApplication.documents).selectinload(SubsidyDocument.attachment),
                selectinload(SubsidyApplication.documents).selectinload(SubsidyDocument.verifier),
                selectinload(SubsidyApplication.history).selectinload(SubsidyStatusHistory.updater),
                selectinload(SubsidyApplication.payments),
            )
            .where(SubsidyApplication.id == id)
        )
        .scalars()
        .first()
    )
    if not app:
        raise HTTPException(status_code=404, detail="Subsidy application not found")

    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        cust = db.execute(select(Customer).where(Customer.user_id == current_user.id)).scalar_one_or_none()
        if not cust or app.customer_id != cust.id:
            raise HTTPException(status_code=403, detail="Access denied to subsidy application")

    docs = [
        SubsidyDocumentResponse(
            id=d.id,
            subsidy_application_id=d.subsidy_application_id,
            document_type=d.document_type,
            attachment_id=d.attachment_id,
            file_name=d.attachment.file_name if d.attachment else None,
            file_path=d.attachment.file_path if d.attachment else None,
            verification_status=d.verification_status,
            remarks=d.remarks,
            verified_by=d.verified_by,
            verifier_name=d.verifier.full_name if d.verifier else None,
            verified_at=d.verified_at,
            created_at=d.created_at,
        )
        for d in app.documents
    ]

    hist = [
        SubsidyStatusHistoryResponse(
            id=h.id,
            subsidy_application_id=h.subsidy_application_id,
            previous_status=h.previous_status,
            new_status=h.new_status,
            action_date=h.action_date,
            comments=h.comments,
            updated_by=h.updated_by,
            updater_name=h.updater.full_name if h.updater else None,
            created_at=h.created_at,
        )
        for h in app.history
    ]

    pays = [
        SubsidyPaymentResponse(
            id=p.id,
            subsidy_application_id=p.subsidy_application_id,
            project_id=p.project_id,
            payment_reference=p.payment_reference,
            disbursement_date=p.disbursement_date,
            disbursed_amount=p.disbursed_amount,
            bank_reference_number=p.bank_reference_number,
            created_at=p.created_at,
        )
        for p in app.payments
    ]

    return APIResponse(
        message="Subsidy application details retrieved",
        data=SubsidyApplicationDetailResponse(
            id=app.id,
            application_number=app.application_number,
            project_id=app.project_id,
            project_code=app.project.project_code if app.project else None,
            customer_id=app.customer_id,
            customer_name=app.customer.full_name if app.customer else None,
            customer_phone=app.customer.phone if app.customer else None,
            portal_registration_number=app.portal_registration_number,
            discom_name=app.discom_name,
            sanctioned_capacity_kw=app.sanctioned_capacity_kw,
            eligible_subsidy_amount=app.eligible_subsidy_amount,
            application_date=app.application_date,
            status=app.status,
            rejection_reason=app.rejection_reason,
            created_by=app.created_by,
            creator_name=app.creator.full_name if app.creator else None,
            created_at=app.created_at,
            updated_at=app.updated_at,
            documents=docs,
            history=hist,
            payments=pays,
        ),
    )


@router.post("/subsidy/applications", response_model=APIResponse[SubsidyApplicationResponse], status_code=status.HTTP_201_CREATED)
def create_subsidy_application(
    payload: SubsidyApplicationCreate,
    current_user: User = Depends(require_subsidy_manager),
    db: Session = Depends(get_db),
):
    project = db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate customer eligibility for PM Surya Ghar National Rooftop Scheme
    customer = db.get(Customer, project.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Associated customer not found")

    cust_type = (customer.customer_type or "").strip().upper()
    if cust_type in {"COMMERCIAL", "INDUSTRIAL"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer type '{customer.customer_type}' is ineligible for PM Surya Ghar subsidy. Central Financial Assistance (CFA) is strictly limited to residential consumers.",
        )
    if cust_type not in {"RESIDENTIAL", "INDIVIDUAL"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer type '{customer.customer_type}' is not recognized as eligible for residential rooftop solar subsidy.",
        )

    # One subsidy application per project
    dup = db.execute(
        select(SubsidyApplication).where(SubsidyApplication.project_id == project.id)
    ).scalar_one_or_none()
    if dup:
        raise HTTPException(
            status_code=400,
            detail=f"Subsidy application '{dup.application_number}' already exists for this project",
        )

    # Portal registration duplicate check
    if payload.portal_registration_number:
        p_dup = db.execute(
            select(SubsidyApplication).where(
                SubsidyApplication.portal_registration_number == payload.portal_registration_number.strip()
            )
        ).scalar_one_or_none()
        if p_dup:
            raise HTTPException(
                status_code=400,
                detail=f"Portal registration number '{payload.portal_registration_number}' is already registered",
            )

    sub_amt = payload.eligible_subsidy_amount
    if sub_amt is None:
        sub_amt = _calculate_standard_subsidy(payload.sanctioned_capacity_kw)

    app_num = _generate_application_number(db)

    app = SubsidyApplication(
        application_number=app_num,
        project_id=project.id,
        customer_id=project.customer_id,
        portal_registration_number=payload.portal_registration_number.strip() if payload.portal_registration_number else None,
        discom_name=payload.discom_name.strip(),
        sanctioned_capacity_kw=payload.sanctioned_capacity_kw,
        eligible_subsidy_amount=sub_amt,
        application_date=payload.application_date,
        status="DRAFT",
        created_by=current_user.id,
    )
    db.add(app)
    db.flush()

    # Initial history log
    hist = SubsidyStatusHistory(
        subsidy_application_id=app.id,
        previous_status=None,
        new_status="DRAFT",
        comments="Subsidy application draft initiated in system",
        updated_by=current_user.id,
    )
    db.add(hist)
    db.commit()
    db.refresh(app)

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="SUBSIDY_APPLICATION_CREATE",
        entity_name="SUBSIDY_APPLICATION",
        entity_id=app.id,
        details={
            "application_number": app.application_number,
            "discom": app.discom_name,
            "eligible_amount": float(app.eligible_subsidy_amount),
        },
    )
    db.commit()

    return APIResponse(
        message=f"Subsidy application '{app.application_number}' created successfully",
        data=SubsidyApplicationResponse(
            id=app.id,
            application_number=app.application_number,
            project_id=app.project_id,
            project_code=project.project_code,
            customer_id=app.customer_id,
            customer_name=project.customer.full_name if project.customer else None,
            customer_phone=project.customer.phone if project.customer else None,
            portal_registration_number=app.portal_registration_number,
            discom_name=app.discom_name,
            sanctioned_capacity_kw=app.sanctioned_capacity_kw,
            eligible_subsidy_amount=app.eligible_subsidy_amount,
            application_date=app.application_date,
            status=app.status,
            rejection_reason=app.rejection_reason,
            created_by=app.created_by,
            creator_name=current_user.full_name,
            created_at=app.created_at,
            updated_at=app.updated_at,
        ),
    )


@router.patch("/subsidy/applications/{id}/status", response_model=APIResponse[SubsidyApplicationResponse])
def update_subsidy_status(
    id: int,
    payload: SubsidyStatusTransitionRequest,
    current_user: User = Depends(require_subsidy_manager),
    db: Session = Depends(get_db),
):
    app = db.get(SubsidyApplication, id)
    if not app:
        raise HTTPException(status_code=404, detail="Subsidy application not found")

    target = payload.status.strip().upper()
    if target not in VALID_SUBSIDY_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid subsidy status '{target}'")

    old_status = app.status
    app.status = target
    if payload.rejection_reason:
        app.rejection_reason = payload.rejection_reason.strip()

    hist = SubsidyStatusHistory(
        subsidy_application_id=app.id,
        previous_status=old_status,
        new_status=target,
        comments=payload.comments or f"Transitioned from {old_status} to {target}",
        updated_by=current_user.id,
    )
    db.add(hist)
    db.commit()
    db.refresh(app)

    project = db.get(Project, app.project_id)

    return APIResponse(
        message=f"Application '{app.application_number}' status updated to '{target}'",
        data=SubsidyApplicationResponse(
            id=app.id,
            application_number=app.application_number,
            project_id=app.project_id,
            project_code=project.project_code if project else None,
            customer_id=app.customer_id,
            customer_name=project.customer.full_name if (project and project.customer) else None,
            customer_phone=project.customer.phone if (project and project.customer) else None,
            portal_registration_number=app.portal_registration_number,
            discom_name=app.discom_name,
            sanctioned_capacity_kw=app.sanctioned_capacity_kw,
            eligible_subsidy_amount=app.eligible_subsidy_amount,
            application_date=app.application_date,
            status=app.status,
            rejection_reason=app.rejection_reason,
            created_by=app.created_by,
            creator_name=current_user.full_name,
            created_at=app.created_at,
            updated_at=app.updated_at,
        ),
    )


# ==========================================
# 2. SUBSIDY DOCUMENTS
# ==========================================

@router.post("/subsidy/applications/{id}/documents", response_model=APIResponse[SubsidyDocumentResponse], status_code=status.HTTP_201_CREATED)
def upload_subsidy_document(
    id: int,
    payload: SubsidyDocumentUploadRequest,
    current_user: User = Depends(require_subsidy_read),
    db: Session = Depends(get_db),
):
    app = db.get(SubsidyApplication, id)
    if not app:
        raise HTTPException(status_code=404, detail="Subsidy application not found")

    doc_type = payload.document_type.strip().upper()
    if doc_type not in VALID_SUBSIDY_DOC_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid document type '{doc_type}'")

    # Create FileAttachment record
    file_att = FileAttachment(
        entity_type="SUBSIDY",
        entity_id=app.id,
        file_name=payload.file_name.strip(),
        file_path=payload.file_path or f"/uploads/subsidy/{app.id}/{payload.file_name.strip()}",
        file_size_bytes=102400,
        mime_type="application/pdf",
        storage_backend="LOCAL",
        uploaded_by=current_user.id,
    )
    db.add(file_att)
    db.flush()

    doc = SubsidyDocument(
        subsidy_application_id=app.id,
        document_type=doc_type,
        attachment_id=file_att.id,
        verification_status="PENDING",
        remarks=payload.remarks,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return APIResponse(
        message=f"Document '{doc.document_type}' uploaded and pending DISCOM verification",
        data=SubsidyDocumentResponse(
            id=doc.id,
            subsidy_application_id=doc.subsidy_application_id,
            document_type=doc.document_type,
            attachment_id=doc.attachment_id,
            file_name=file_att.file_name,
            file_path=file_att.file_path,
            verification_status=doc.verification_status,
            remarks=doc.remarks,
            verified_by=doc.verified_by,
            verifier_name=None,
            verified_at=doc.verified_at,
            created_at=doc.created_at,
        ),
    )


@router.patch("/subsidy/documents/{doc_id}/verify", response_model=APIResponse[SubsidyDocumentResponse])
def verify_subsidy_document(
    doc_id: int,
    payload: SubsidyDocumentVerificationRequest,
    current_user: User = Depends(require_subsidy_manager),
    db: Session = Depends(get_db),
):
    doc = db.get(SubsidyDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Subsidy document not found")

    v_st = payload.verification_status.strip().upper()
    if v_st not in VALID_DOC_VERIFICATION_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid verification status '{v_st}'")

    doc.verification_status = v_st
    doc.remarks = payload.remarks
    doc.verified_by = current_user.id
    doc.verified_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(doc)

    att = db.get(FileAttachment, doc.attachment_id)

    return APIResponse(
        message=f"Document '{doc.document_type}' verified as '{v_st}'",
        data=SubsidyDocumentResponse(
            id=doc.id,
            subsidy_application_id=doc.subsidy_application_id,
            document_type=doc.document_type,
            attachment_id=doc.attachment_id,
            file_name=att.file_name if att else None,
            file_path=att.file_path if att else None,
            verification_status=doc.verification_status,
            remarks=doc.remarks,
            verified_by=doc.verified_by,
            verifier_name=current_user.full_name,
            verified_at=doc.verified_at,
            created_at=doc.created_at,
        ),
    )


# ==========================================
# 3. SUBSIDY DISBURSEMENT PAYMENTS
# ==========================================

@router.post("/subsidy/applications/{id}/disbursements", response_model=APIResponse[SubsidyPaymentResponse], status_code=status.HTTP_201_CREATED)
def record_subsidy_disbursement(
    id: int,
    payload: SubsidyPaymentCreate,
    current_user: User = Depends(require_subsidy_manager),
    db: Session = Depends(get_db),
):
    app = db.get(SubsidyApplication, id)
    if not app:
        raise HTTPException(status_code=404, detail="Subsidy application not found")

    pay_ref = payload.payment_reference or _generate_subsidy_payment_ref(db)

    # Duplicate payment check
    dup = db.execute(select(SubsidyPayment).where(SubsidyPayment.payment_reference == pay_ref)).scalar_one_or_none()
    if dup:
        raise HTTPException(status_code=400, detail=f"Payment reference '{pay_ref}' already recorded")

    pay = SubsidyPayment(
        subsidy_application_id=app.id,
        project_id=app.project_id,
        payment_reference=pay_ref,
        disbursement_date=payload.disbursement_date,
        disbursed_amount=payload.disbursed_amount,
        bank_reference_number=payload.bank_reference_number,
    )
    db.add(pay)

    # Transition application status to SUBSIDY_DISBURSED
    old_status = app.status
    app.status = "SUBSIDY_DISBURSED"

    hist = SubsidyStatusHistory(
        subsidy_application_id=app.id,
        previous_status=old_status,
        new_status="SUBSIDY_DISBURSED",
        comments=f"Subsidy amount ₹{payload.disbursed_amount} successfully disbursed. Ref: {pay_ref}",
        updated_by=current_user.id,
    )
    db.add(hist)
    db.commit()
    db.refresh(pay)

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="SUBSIDY_DISBURSED",
        entity_name="SUBSIDY_APPLICATION",
        entity_id=app.id,
        details={"payment_reference": pay_ref, "amount": float(payload.disbursed_amount)},
    )
    db.commit()

    return APIResponse(
        message=f"Subsidy disbursement of ₹{pay.disbursed_amount} recorded under ref '{pay.payment_reference}'",
        data=SubsidyPaymentResponse(
            id=pay.id,
            subsidy_application_id=pay.subsidy_application_id,
            project_id=pay.project_id,
            payment_reference=pay.payment_reference,
            disbursement_date=pay.disbursement_date,
            disbursed_amount=pay.disbursed_amount,
            bank_reference_number=pay.bank_reference_number,
            created_at=pay.created_at,
        ),
    )
