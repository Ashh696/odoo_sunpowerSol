from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_, desc
from datetime import datetime, date, timezone, timedelta
import math

from app.database import get_db
from app.models.auth import User, Role, Employee
from app.models.workflow import AuditLog
from app.models.crm import Customer, Product
from app.models.projects import Project
from app.models.inventory import SerialNumber, SerialNumberHistory, Inventory, StockMovement
from app.models.warranty import (
    WarrantyPolicy,
    WarrantyRecord,
    WarrantyEvent,
    ServiceTicket,
    ServiceVisit,
    Replacement,
    ServiceTicketConfirmation,
)
from app.schemas.warranty import (
    WarrantyPolicyCreate,
    WarrantyPolicyResponse,
    WarrantyRecordCreate,
    ProjectWarrantyBatchRegister,
    WarrantyRecordResponse,
    WarrantyRecordDetailResponse,
    WarrantyEventCreate,
    WarrantyEventResponse,
    ServiceTicketCreate,
    ServiceTicketStatusUpdate,
    ServiceTicketResponse,
    ServiceTicketDetailResponse,
    ServiceVisitCreate,
    ServiceVisitComplete,
    ServiceVisitResponse,
    ComponentReplacementCreate,
    ReplacementResponse,
    ServiceTicketConfirmationCreate,
    ServiceTicketConfirmationResponse,
    ServiceTicketSLAMetrics,
    VALID_WARRANTY_STATUSES,
    VALID_WARRANTY_EVENT_TYPES,
    VALID_TICKET_CATEGORIES,
    VALID_TICKET_PRIORITIES,
    VALID_TICKET_STATUSES,
    VALID_VISIT_STATUSES,
)
from app.schemas import APIResponse
from app.dependencies.auth import get_current_user
from app.utils.roles import SystemRole

router = APIRouter(tags=["Warranty & Service Management"])


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


def require_service_access(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role and current_user.role.slug in {
        SystemRole.SUPER_ADMIN,
        SystemRole.DIRECTOR,
        SystemRole.TECHNICAL_MANAGER,
        SystemRole.SERVICE_WARRANTY,
        SystemRole.FIELD_TECHNICIAN,
        SystemRole.CUSTOMER,
    }:
        return current_user
    raise HTTPException(status_code=403, detail="Unauthorized to access service operations")


def require_service_staff(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role and current_user.role.slug in {
        SystemRole.SUPER_ADMIN,
        SystemRole.DIRECTOR,
        SystemRole.TECHNICAL_MANAGER,
        SystemRole.SERVICE_WARRANTY,
    }:
        return current_user
    raise HTTPException(status_code=403, detail="Service staff authorization required")


def _generate_cert_number(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"CERT-{year}-"
    latest = (
        db.execute(
            select(WarrantyRecord.certificate_number)
            .where(WarrantyRecord.certificate_number.like(f"{prefix}%"))
            .order_by(WarrantyRecord.certificate_number.desc())
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


def _generate_ticket_number(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"TKT-{year}-"
    latest = (
        db.execute(
            select(ServiceTicket.ticket_number)
            .where(ServiceTicket.ticket_number.like(f"{prefix}%"))
            .order_by(ServiceTicket.ticket_number.desc())
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
# 1. WARRANTY POLICIES
# ==========================================

@router.get("/warranty/policies", response_model=APIResponse[List[WarrantyPolicyResponse]])
def list_warranty_policies(
    current_user: User = Depends(require_service_access),
    db: Session = Depends(get_db),
):
    policies = (
        db.execute(
            select(WarrantyPolicy)
            .options(selectinload(WarrantyPolicy.product))
            .order_by(WarrantyPolicy.created_at.desc())
        )
        .scalars()
        .all()
    )
    items = [
        WarrantyPolicyResponse(
            id=p.id,
            policy_code=p.policy_code,
            name=p.name,
            product_id=p.product_id,
            product_name=p.product.name if p.product else None,
            warranty_period_months=p.warranty_period_months,
            activation_trigger=p.activation_trigger,
            terms_and_conditions=p.terms_and_conditions,
            is_active=p.is_active,
            created_at=p.created_at,
        )
        for p in policies
    ]
    return APIResponse(message="Warranty policies retrieved", data=items)


@router.post("/warranty/policies", response_model=APIResponse[WarrantyPolicyResponse], status_code=status.HTTP_201_CREATED)
def create_warranty_policy(
    payload: WarrantyPolicyCreate,
    current_user: User = Depends(require_service_staff),
    db: Session = Depends(get_db),
):
    dup = db.execute(select(WarrantyPolicy).where(WarrantyPolicy.policy_code == payload.policy_code.strip())).scalar_one_or_none()
    if dup:
        raise HTTPException(status_code=400, detail=f"Policy code '{payload.policy_code}' already exists")

    if payload.product_id:
        prod = db.get(Product, payload.product_id)
        if not prod:
            raise HTTPException(status_code=404, detail="Product not found")

    policy = WarrantyPolicy(
        policy_code=payload.policy_code.strip(),
        name=payload.name.strip(),
        product_id=payload.product_id,
        warranty_period_months=payload.warranty_period_months,
        activation_trigger=payload.activation_trigger,
        terms_and_conditions=payload.terms_and_conditions,
        is_active=payload.is_active,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)

    return APIResponse(
        message=f"Warranty policy '{policy.policy_code}' created",
        data=WarrantyPolicyResponse(
            id=policy.id,
            policy_code=policy.policy_code,
            name=policy.name,
            product_id=policy.product_id,
            product_name=policy.product.name if policy.product else None,
            warranty_period_months=policy.warranty_period_months,
            activation_trigger=policy.activation_trigger,
            terms_and_conditions=policy.terms_and_conditions,
            is_active=policy.is_active,
            created_at=policy.created_at,
        ),
    )


# ==========================================
# 2. WARRANTY RECORDS
# ==========================================

@router.get("/warranty", response_model=APIResponse[dict])
@router.get("/warranty/records", response_model=APIResponse[dict])
def list_warranty_records(
    project_id: Optional[int] = Query(None),
    customer_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    serial_number: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_service_access),
    db: Session = Depends(get_db),
):
    query = (
        select(WarrantyRecord)
        .options(
            selectinload(WarrantyRecord.project),
            selectinload(WarrantyRecord.product),
            selectinload(WarrantyRecord.serial),
            selectinload(WarrantyRecord.customer),
            selectinload(WarrantyRecord.policy),
        )
    )

    # Customer isolation
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        cust = db.execute(select(Customer).where(Customer.user_id == current_user.id)).scalar_one_or_none()
        if not cust:
            return APIResponse(message="No warranty records found", data={"items": [], "total": 0, "page": 1, "page_size": page_size, "total_pages": 0})
        query = query.where(WarrantyRecord.customer_id == cust.id)
    else:
        if customer_id:
            query = query.where(WarrantyRecord.customer_id == customer_id)

    if project_id:
        query = query.where(WarrantyRecord.project_id == project_id)
    if status_filter:
        query = query.where(WarrantyRecord.status == status_filter.strip().upper())
    if serial_number:
        query = query.join(WarrantyRecord.serial).where(SerialNumber.serial_number.ilike(f"%{serial_number.strip()}%"))

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0

    records = (
        db.execute(
            query.order_by(WarrantyRecord.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    items = [
        WarrantyRecordResponse(
            id=r.id,
            certificate_number=r.certificate_number,
            project_id=r.project_id,
            project_code=r.project.project_code if r.project else None,
            product_id=r.product_id,
            product_name=r.product.name if r.product else None,
            product_sku=r.product.product_code if r.product else None,
            serial_number_id=r.serial_number_id,
            serial_number=r.serial.serial_number if r.serial else None,
            customer_id=r.customer_id,
            customer_name=r.customer.full_name if r.customer else None,
            warranty_policy_id=r.warranty_policy_id,
            policy_name=r.policy.name if r.policy else None,
            warranty_period_months=r.policy.warranty_period_months if r.policy else None,
            delivery_date=r.delivery_date,
            activation_trigger=r.activation_trigger,
            activation_date=r.activation_date,
            warranty_start_date=r.warranty_start_date,
            warranty_end_date=r.warranty_end_date,
            status=r.status,
            created_at=r.created_at,
        )
        for r in records
    ]

    return APIResponse(
        message="Warranty records retrieved",
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        },
    )


@router.get("/warranty/records/{id}", response_model=APIResponse[WarrantyRecordDetailResponse])
def get_warranty_record(
    id: int,
    current_user: User = Depends(require_service_access),
    db: Session = Depends(get_db),
):
    rec = (
        db.execute(
            select(WarrantyRecord)
            .options(
                selectinload(WarrantyRecord.project),
                selectinload(WarrantyRecord.product),
                selectinload(WarrantyRecord.serial),
                selectinload(WarrantyRecord.customer),
                selectinload(WarrantyRecord.policy),
                selectinload(WarrantyRecord.events).selectinload(WarrantyEvent.recorder),
            )
            .where(WarrantyRecord.id == id)
        )
        .scalars()
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Warranty record not found")

    # Customer isolation
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        cust = db.execute(select(Customer).where(Customer.user_id == current_user.id)).scalar_one_or_none()
        if not cust or rec.customer_id != cust.id:
            raise HTTPException(status_code=403, detail="Access denied to warranty record")

    events = [
        WarrantyEventResponse(
            id=e.id,
            warranty_record_id=e.warranty_record_id,
            event_type=e.event_type,
            event_date=e.event_date,
            description=e.description,
            recorded_by=e.recorded_by,
            recorder_name=e.recorder.full_name if e.recorder else None,
            created_at=e.created_at,
        )
        for e in rec.events
    ]

    return APIResponse(
        message="Warranty record retrieved",
        data=WarrantyRecordDetailResponse(
            id=rec.id,
            certificate_number=rec.certificate_number,
            project_id=rec.project_id,
            project_code=rec.project.project_code if rec.project else None,
            product_id=rec.product_id,
            product_name=rec.product.name if rec.product else None,
            product_sku=rec.product.product_code if rec.product else None,
            serial_number_id=rec.serial_number_id,
            serial_number=rec.serial.serial_number if rec.serial else None,
            customer_id=rec.customer_id,
            customer_name=rec.customer.full_name if rec.customer else None,
            warranty_policy_id=rec.warranty_policy_id,
            policy_name=rec.policy.name if rec.policy else None,
            warranty_period_months=rec.policy.warranty_period_months if rec.policy else None,
            delivery_date=rec.delivery_date,
            activation_trigger=rec.activation_trigger,
            activation_date=rec.activation_date,
            warranty_start_date=rec.warranty_start_date,
            warranty_end_date=rec.warranty_end_date,
            status=rec.status,
            created_at=rec.created_at,
            events=events,
        ),
    )


@router.post("/projects/{id}/warranty-register", response_model=APIResponse[List[WarrantyRecordResponse]], status_code=status.HTTP_201_CREATED)
def register_project_warranties(
    id: int,
    payload: Optional[ProjectWarrantyBatchRegister] = None,
    current_user: User = Depends(require_service_staff),
    db: Session = Depends(get_db),
):
    """
    Register warranty certificates for all serialized equipment installed on a project.
    Creates WarrantyRecord and logs initial ACTIVATION event.
    """
    project = db.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    act_date = (payload.activation_date if payload else None) or date.today()

    # Find all serials associated with this project (via SerialNumberHistory or SerialNumber)
    serials_query = (
        select(SerialNumber)
        .join(SerialNumberHistory, SerialNumber.id == SerialNumberHistory.serial_number_id)
        .where(
            SerialNumberHistory.project_id == project.id,
            SerialNumber.status.in_(["INSTALLED", "DISPATCHED"]),
        )
        .distinct()
    )
    serials = db.execute(serials_query).scalars().all()

    if not serials:
        # Fallback: check if serials are installed
        serials = (
            db.execute(
                select(SerialNumber)
                .where(SerialNumber.status == "INSTALLED")
            )
            .scalars()
            .all()
        )

    if not serials:
        raise HTTPException(
            status_code=400,
            detail="No installed serialized equipment found for this project to register warranty",
        )

    # Find or create default warranty policy
    default_policy = db.execute(select(WarrantyPolicy).where(WarrantyPolicy.is_active == True)).scalars().first()
    if not default_policy:
        default_policy = WarrantyPolicy(
            policy_code="POL-STD-60M",
            name="Standard 5-Year Comprehensive Solar Warranty",
            warranty_period_months=60,
            activation_trigger="COMMISSIONING",
            terms_and_conditions="Comprehensive coverage for inverters, panels and mounting structures against manufacturing defects.",
            is_active=True,
        )
        db.add(default_policy)
        db.flush()

    registered_records = []
    for sn in serials:
        # Check if already registered
        existing = db.execute(
            select(WarrantyRecord).where(
                WarrantyRecord.project_id == project.id,
                WarrantyRecord.serial_number_id == sn.id,
            )
        ).scalar_one_or_none()

        if existing:
            registered_records.append(existing)
            continue

        # Look up product-specific policy or default
        policy = db.execute(
            select(WarrantyPolicy).where(
                WarrantyPolicy.product_id == sn.product_id,
                WarrantyPolicy.is_active == True,
            )
        ).scalars().first() or default_policy

        months = policy.warranty_period_months or sn.warranty_months or 60
        cert_num = _generate_cert_number(db)
        start_d = act_date
        end_d = start_d + timedelta(days=int(months * 30.4375))

        rec = WarrantyRecord(
            certificate_number=cert_num,
            project_id=project.id,
            product_id=sn.product_id,
            serial_number_id=sn.id,
            customer_id=project.customer_id,
            warranty_policy_id=policy.id,
            delivery_date=sn.received_date or act_date,
            activation_trigger="COMMISSIONING",
            activation_date=act_date,
            warranty_start_date=start_d,
            warranty_end_date=end_d,
            status="ACTIVE",
        )
        db.add(rec)
        db.flush()

        event = WarrantyEvent(
            warranty_record_id=rec.id,
            event_type="ACTIVATION",
            description=f"Warranty successfully activated on commissioning of project {project.project_code}",
            recorded_by=current_user.id,
        )
        db.add(event)
        registered_records.append(rec)

    db.commit()

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="PROJECT_WARRANTY_REGISTER",
        entity_name="PROJECT",
        entity_id=project.id,
        details={"certificates_count": len(registered_records)},
    )
    db.commit()

    # Build response
    resp = []
    for r in registered_records:
        db.refresh(r)
        resp.append(
            WarrantyRecordResponse(
                id=r.id,
                certificate_number=r.certificate_number,
                project_id=r.project_id,
                project_code=project.project_code,
                product_id=r.product_id,
                product_name=r.product.name if r.product else None,
                product_sku=r.product.product_code if r.product else None,
                serial_number_id=r.serial_number_id,
                serial_number=r.serial.serial_number if r.serial else None,
                customer_id=r.customer_id,
                customer_name=project.customer.full_name if project.customer else None,
                warranty_policy_id=r.warranty_policy_id,
                policy_name=r.policy.name if r.policy else None,
                warranty_period_months=r.policy.warranty_period_months if r.policy else None,
                delivery_date=r.delivery_date,
                activation_trigger=r.activation_trigger,
                activation_date=r.activation_date,
                warranty_start_date=r.warranty_start_date,
                warranty_end_date=r.warranty_end_date,
                status=r.status,
                created_at=r.created_at,
            )
        )

    return APIResponse(
        message=f"{len(resp)} warranty certificate(s) registered for project '{project.project_code}'",
        data=resp,
    )


# ==========================================
# 3. SERVICE TICKETS
# ==========================================

@router.get("/service-tickets", response_model=APIResponse[dict])
def list_service_tickets(
    project_id: Optional[int] = Query(None),
    customer_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_service_access),
    db: Session = Depends(get_db),
):
    query = (
        select(ServiceTicket)
        .options(
            selectinload(ServiceTicket.project),
            selectinload(ServiceTicket.customer),
            selectinload(ServiceTicket.serial),
            selectinload(ServiceTicket.warranty_record),
            selectinload(ServiceTicket.creator),
        )
    )

    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        cust = db.execute(select(Customer).where(Customer.user_id == current_user.id)).scalar_one_or_none()
        if not cust:
            return APIResponse(message="No service tickets found", data={"items": [], "total": 0, "page": 1, "page_size": page_size, "total_pages": 0})
        query = query.where(ServiceTicket.customer_id == cust.id)
    else:
        if customer_id:
            query = query.where(ServiceTicket.customer_id == customer_id)

    if project_id:
        query = query.where(ServiceTicket.project_id == project_id)
    if status_filter:
        query = query.where(ServiceTicket.status == status_filter.strip().upper())
    if priority_filter:
        query = query.where(ServiceTicket.priority == priority_filter.strip().upper())

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0

    tickets = (
        db.execute(
            query.order_by(ServiceTicket.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    items = [
        ServiceTicketResponse(
            id=t.id,
            ticket_number=t.ticket_number,
            project_id=t.project_id,
            project_code=t.project.project_code if t.project else None,
            customer_id=t.customer_id,
            customer_name=t.customer.full_name if t.customer else None,
            serial_number_id=t.serial_number_id,
            serial_number=t.serial.serial_number if t.serial else None,
            warranty_record_id=t.warranty_record_id,
            certificate_number=t.warranty_record.certificate_number if t.warranty_record else None,
            issue_category=t.issue_category,
            priority=t.priority,
            description=t.description,
            status=t.status,
            created_by=t.created_by,
            creator_name=t.creator.full_name if t.creator else None,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in tickets
    ]

    return APIResponse(
        message="Service tickets retrieved",
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        },
    )


@router.get("/service-tickets/{id}", response_model=APIResponse[ServiceTicketDetailResponse])
def get_service_ticket(
    id: int,
    current_user: User = Depends(require_service_access),
    db: Session = Depends(get_db),
):
    ticket = (
        db.execute(
            select(ServiceTicket)
            .options(
                selectinload(ServiceTicket.project),
                selectinload(ServiceTicket.customer),
                selectinload(ServiceTicket.serial),
                selectinload(ServiceTicket.warranty_record),
                selectinload(ServiceTicket.creator),
                selectinload(ServiceTicket.visits).selectinload(ServiceVisit.technician).selectinload(Employee.user),
                selectinload(ServiceTicket.replacements).selectinload(Replacement.original_serial),
                selectinload(ServiceTicket.replacements).selectinload(Replacement.replacement_serial),
                selectinload(ServiceTicket.replacements).selectinload(Replacement.replacer).selectinload(Employee.user),
                selectinload(ServiceTicket.confirmation),
            )
            .where(ServiceTicket.id == id)
        )
        .scalars()
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Service ticket not found")

    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        cust = db.execute(select(Customer).where(Customer.user_id == current_user.id)).scalar_one_or_none()
        if not cust or ticket.customer_id != cust.id:
            raise HTTPException(status_code=403, detail="Access denied to service ticket")

    visits_resp = [
        ServiceVisitResponse(
            id=v.id,
            ticket_id=v.ticket_id,
            technician_id=v.technician_id,
            technician_name=v.technician.user.full_name if (v.technician and v.technician.user) else None,
            visit_number=v.visit_number,
            scheduled_date=v.scheduled_date,
            visit_status=v.visit_status,
            actual_start=v.actual_start,
            actual_end=v.actual_end,
            findings=v.findings,
            action_taken=v.action_taken,
            parts_replaced=v.parts_replaced,
            customer_present_name=v.customer_present_name,
            created_at=v.created_at,
        )
        for v in ticket.visits
    ]

    replacements_resp = [
        ReplacementResponse(
            id=rep.id,
            ticket_id=rep.ticket_id,
            original_serial_id=rep.original_serial_id,
            original_serial_number=rep.original_serial.serial_number if rep.original_serial else None,
            replacement_serial_id=rep.replacement_serial_id,
            replacement_serial_number=rep.replacement_serial.serial_number if rep.replacement_serial else None,
            replacement_reason=rep.replacement_reason,
            replacement_date=rep.replacement_date,
            replaced_by=rep.replaced_by,
            replacer_name=rep.replacer.user.full_name if (rep.replacer and rep.replacer.user) else None,
            created_at=rep.created_at,
        )
        for rep in ticket.replacements
    ]

    conf_resp = None
    if ticket.confirmation:
        conf_resp = ServiceTicketConfirmationResponse(
            id=ticket.confirmation.id,
            ticket_id=ticket.confirmation.ticket_id,
            customer_id=ticket.confirmation.customer_id,
            resolution_confirmed=ticket.confirmation.resolution_confirmed,
            customer_rating=ticket.confirmation.customer_rating,
            customer_feedback=ticket.confirmation.customer_feedback,
            confirmed_at=ticket.confirmation.confirmed_at,
            confirmation_channel=ticket.confirmation.confirmation_channel,
            created_at=ticket.confirmation.created_at,
        )

    return APIResponse(
        message="Service ticket detail retrieved",
        data=ServiceTicketDetailResponse(
            id=ticket.id,
            ticket_number=ticket.ticket_number,
            project_id=ticket.project_id,
            project_code=ticket.project.project_code if ticket.project else None,
            customer_id=ticket.customer_id,
            customer_name=ticket.customer.full_name if ticket.customer else None,
            serial_number_id=ticket.serial_number_id,
            serial_number=ticket.serial.serial_number if ticket.serial else None,
            warranty_record_id=ticket.warranty_record_id,
            certificate_number=ticket.warranty_record.certificate_number if ticket.warranty_record else None,
            issue_category=ticket.issue_category,
            priority=ticket.priority,
            description=ticket.description,
            status=ticket.status,
            created_by=ticket.created_by,
            creator_name=ticket.creator.full_name if ticket.creator else None,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            visits=visits_resp,
            replacements=replacements_resp,
            confirmation=conf_resp,
        ),
    )


@router.post("/service-tickets", response_model=APIResponse[ServiceTicketResponse], status_code=status.HTTP_201_CREATED)
def create_service_ticket(
    payload: ServiceTicketCreate,
    current_user: User = Depends(require_service_access),
    db: Session = Depends(get_db),
):
    project = db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # If created by customer, verify ownership
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        cust = db.execute(select(Customer).where(Customer.user_id == current_user.id)).scalar_one_or_none()
        if not cust or project.customer_id != cust.id:
            raise HTTPException(status_code=403, detail="Customer can only create tickets for their own projects")

    cat = payload.issue_category.strip().upper()
    if cat not in VALID_TICKET_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid issue category '{cat}'")

    prio = payload.priority.strip().upper()
    if prio not in VALID_TICKET_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Invalid priority '{prio}'")

    ticket_num = _generate_ticket_number(db)

    ticket = ServiceTicket(
        ticket_number=ticket_num,
        project_id=project.id,
        customer_id=project.customer_id,
        serial_number_id=payload.serial_number_id,
        warranty_record_id=payload.warranty_record_id,
        issue_category=cat,
        priority=prio,
        description=payload.description.strip(),
        status="OPEN",
        created_by=current_user.id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # If warranty record is associated, log claim event
    if payload.warranty_record_id:
        event = WarrantyEvent(
            warranty_record_id=payload.warranty_record_id,
            event_type="CLAIM_RAISED",
            description=f"Service ticket {ticket.ticket_number} created: {ticket.description[:100]}",
            recorded_by=current_user.id,
        )
        db.add(event)
        db.commit()

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="SERVICE_TICKET_CREATE",
        entity_name="SERVICE_TICKET",
        entity_id=ticket.id,
        details={"ticket_number": ticket.ticket_number, "priority": ticket.priority},
    )
    db.commit()

    return APIResponse(
        message=f"Service ticket '{ticket.ticket_number}' created successfully",
        data=ServiceTicketResponse(
            id=ticket.id,
            ticket_number=ticket.ticket_number,
            project_id=ticket.project_id,
            project_code=project.project_code,
            customer_id=ticket.customer_id,
            customer_name=project.customer.full_name if project.customer else None,
            serial_number_id=ticket.serial_number_id,
            serial_number=ticket.serial.serial_number if ticket.serial else None,
            warranty_record_id=ticket.warranty_record_id,
            certificate_number=ticket.warranty_record.certificate_number if ticket.warranty_record else None,
            issue_category=ticket.issue_category,
            priority=ticket.priority,
            description=ticket.description,
            status=ticket.status,
            created_by=ticket.created_by,
            creator_name=current_user.full_name,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
        ),
    )


@router.patch("/service-tickets/{id}/status", response_model=APIResponse[ServiceTicketResponse])
def update_service_ticket_status(
    id: int,
    payload: ServiceTicketStatusUpdate,
    current_user: User = Depends(require_service_staff),
    db: Session = Depends(get_db),
):
    ticket = db.get(ServiceTicket, id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Service ticket not found")

    target = payload.status.strip().upper()
    if target not in VALID_TICKET_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid ticket status '{target}'")

    ticket.status = target
    db.commit()
    db.refresh(ticket)

    project = db.get(Project, ticket.project_id)
    cust = db.get(Customer, ticket.customer_id)

    return APIResponse(
        message=f"Ticket '{ticket.ticket_number}' status updated to '{target}'",
        data=ServiceTicketResponse(
            id=ticket.id,
            ticket_number=ticket.ticket_number,
            project_id=ticket.project_id,
            project_code=project.project_code if project else None,
            customer_id=ticket.customer_id,
            customer_name=cust.full_name if cust else None,
            serial_number_id=ticket.serial_number_id,
            serial_number=ticket.serial.serial_number if ticket.serial else None,
            warranty_record_id=ticket.warranty_record_id,
            certificate_number=ticket.warranty_record.certificate_number if ticket.warranty_record else None,
            issue_category=ticket.issue_category,
            priority=ticket.priority,
            description=ticket.description,
            status=ticket.status,
            created_by=ticket.created_by,
            creator_name=current_user.full_name,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
        ),
    )


# ==========================================
# 4. SERVICE VISITS
# ==========================================

@router.post("/service-tickets/{id}/visits", response_model=APIResponse[ServiceVisitResponse], status_code=status.HTTP_201_CREATED)
def schedule_service_visit(
    id: int,
    payload: ServiceVisitCreate,
    current_user: User = Depends(require_service_staff),
    db: Session = Depends(get_db),
):
    ticket = db.get(ServiceTicket, id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Service ticket not found")

    emp = db.get(Employee, payload.technician_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Technician employee not found")

    visit_count = db.execute(
        select(func.count(ServiceVisit.id)).where(ServiceVisit.ticket_id == ticket.id)
    ).scalar() or 0

    visit = ServiceVisit(
        ticket_id=ticket.id,
        technician_id=emp.id,
        visit_number=visit_count + 1,
        scheduled_date=payload.scheduled_date,
        visit_status="SCHEDULED",
    )
    db.add(visit)

    # Transition ticket to ASSIGNED or IN_PROGRESS
    if ticket.status == "OPEN":
        ticket.status = "ASSIGNED"

    db.commit()
    db.refresh(visit)

    return APIResponse(
        message=f"Visit #{visit.visit_number} scheduled for technician on {visit.scheduled_date}",
        data=ServiceVisitResponse(
            id=visit.id,
            ticket_id=visit.ticket_id,
            technician_id=visit.technician_id,
            technician_name=emp.user.full_name if emp.user else None,
            visit_number=visit.visit_number,
            scheduled_date=visit.scheduled_date,
            visit_status=visit.visit_status,
            actual_start=visit.actual_start,
            actual_end=visit.actual_end,
            findings=visit.findings,
            action_taken=visit.action_taken,
            parts_replaced=visit.parts_replaced,
            customer_present_name=visit.customer_present_name,
            created_at=visit.created_at,
        ),
    )


@router.patch("/service-visits/{id}/complete", response_model=APIResponse[ServiceVisitResponse])
def complete_service_visit(
    id: int,
    payload: ServiceVisitComplete,
    current_user: User = Depends(require_service_access),
    db: Session = Depends(get_db),
):
    visit = db.get(ServiceVisit, id)
    if not visit:
        raise HTTPException(status_code=404, detail="Service visit not found")

    visit.findings = payload.findings.strip()
    visit.action_taken = payload.action_taken.strip()
    visit.parts_replaced = payload.parts_replaced
    visit.customer_present_name = payload.customer_present_name
    visit.visit_status = "COMPLETED"
    visit.actual_start = visit.actual_start or datetime.now(timezone.utc) - timedelta(hours=2)
    visit.actual_end = datetime.now(timezone.utc)

    # If ticket was in progress or assigned, update to IN_PROGRESS or RESOLVED
    ticket = db.get(ServiceTicket, visit.ticket_id)
    if ticket and ticket.status in {"OPEN", "ASSIGNED"}:
        ticket.status = "IN_PROGRESS"

    db.commit()
    db.refresh(visit)

    emp = db.get(Employee, visit.technician_id)

    return APIResponse(
        message="Service visit completed and findings recorded",
        data=ServiceVisitResponse(
            id=visit.id,
            ticket_id=visit.ticket_id,
            technician_id=visit.technician_id,
            technician_name=emp.user.full_name if (emp and emp.user) else None,
            visit_number=visit.visit_number,
            scheduled_date=visit.scheduled_date,
            visit_status=visit.visit_status,
            actual_start=visit.actual_start,
            actual_end=visit.actual_end,
            findings=visit.findings,
            action_taken=visit.action_taken,
            parts_replaced=visit.parts_replaced,
            customer_present_name=visit.customer_present_name,
            created_at=visit.created_at,
        ),
    )


# ==========================================
# 5. COMPONENT REPLACEMENTS
# ==========================================

@router.post("/service-tickets/{id}/replacements", response_model=APIResponse[ReplacementResponse], status_code=status.HTTP_201_CREATED)
def replace_component_under_warranty(
    id: int,
    payload: ComponentReplacementCreate,
    current_user: User = Depends(require_service_staff),
    db: Session = Depends(get_db),
):
    """
    Atomically swap defective serialized component with a healthy replacement serial.
    - Transitions original serial status -> DEFECTIVE
    - Transitions replacement serial status -> INSTALLED
    - Records replacement log
    - Records WarrantyEvent on associated warranty record
    """
    ticket = db.get(ServiceTicket, id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Service ticket not found")

    orig_sn = db.execute(select(SerialNumber).where(SerialNumber.id == payload.original_serial_id).with_for_update()).scalar_one_or_none()
    if not orig_sn:
        raise HTTPException(status_code=404, detail="Original serial number not found")

    rep_sn = db.execute(select(SerialNumber).where(SerialNumber.id == payload.replacement_serial_id).with_for_update()).scalar_one_or_none()
    if not rep_sn:
        raise HTTPException(status_code=404, detail="Replacement serial number not found")

    if orig_sn.id == rep_sn.id:
        raise HTTPException(status_code=400, detail="Replacement serial cannot be identical to original serial")

    # Prevent duplicate replacement on the same ticket or original serial
    existing_rep = db.execute(
        select(Replacement).where(
            Replacement.ticket_id == ticket.id,
            Replacement.original_serial_id == orig_sn.id,
        )
    ).scalar_one_or_none()
    if existing_rep:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Original component '{orig_sn.serial_number}' has already been replaced under this ticket (Replacement ID: {existing_rep.id}).",
        )

    if orig_sn.status == "DEFECTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Original component '{orig_sn.serial_number}' is already marked DEFECTIVE and cannot be replaced again.",
        )

    # Validate replacement serial is IN_STOCK and matches product
    if rep_sn.status != "IN_STOCK":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Replacement serial '{rep_sn.serial_number}' is not available in warehouse stock (Current status: '{rep_sn.status}').",
        )

    if rep_sn.product_id != orig_sn.product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Replacement component product ID ({rep_sn.product_id}) does not match original component product ID ({orig_sn.product_id}). Cross-product replacement is not permitted.",
        )

    # Validate warehouse inventory availability and row-lock inventory
    inv = db.execute(
        select(Inventory).where(Inventory.product_id == rep_sn.product_id).with_for_update()
    ).scalar_one_or_none()

    if not inv or inv.quantity_available < Decimal("1.00") or inv.quantity_on_hand < Decimal("1.00"):
        avail_stock = inv.quantity_available if inv else Decimal("0.00")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient warehouse stock for replacement product. Available: {avail_stock}, Required: 1.00",
        )

    # Find employee profile of current user or assign primary technician
    emp = db.execute(select(Employee).where(Employee.user_id == current_user.id)).scalar_one_or_none()
    if not emp:
        emp = db.execute(select(Employee)).scalars().first()
        if not emp:
            raise HTTPException(status_code=400, detail="No employee record found for technician replacement authorization")

    # 1. Deduct warehouse stock and record StockMovement
    old_qoh = inv.quantity_on_hand
    inv.quantity_on_hand -= Decimal("1.00")
    inv.quantity_available = max(Decimal("0.00"), inv.quantity_on_hand - inv.reserved_quantity)
    new_qoh = inv.quantity_on_hand

    movement = StockMovement(
        inventory_id=inv.id,
        product_id=rep_sn.product_id,
        movement_type="ADJUSTMENT",
        reference_type="SERVICE_TICKET",
        reference_id=ticket.id,
        quantity=-Decimal("1.00"),
        unit_cost=inv.average_unit_cost,
        quantity_before=old_qoh,
        quantity_after=new_qoh,
        performed_by=current_user.id,
        remarks=f"Warranty replacement under ticket {ticket.ticket_number} for defective serial {orig_sn.serial_number}",
    )
    db.add(movement)

    # 2. Update original serial to DEFECTIVE
    old_orig_status = orig_sn.status
    orig_sn.status = "DEFECTIVE"

    h1 = SerialNumberHistory(
        serial_number_id=orig_sn.id,
        action_taken="DEFECT_REPLACED",
        previous_status=old_orig_status,
        new_status="DEFECTIVE",
        project_id=ticket.project_id,
        recorded_by=current_user.id,
        remarks=f"Replaced under ticket {ticket.ticket_number}: {payload.replacement_reason}",
    )
    db.add(h1)

    # 3. Update replacement serial to INSTALLED
    old_rep_status = rep_sn.status
    rep_sn.status = "INSTALLED"
    rep_sn.project_id = ticket.project_id

    h2 = SerialNumberHistory(
        serial_number_id=rep_sn.id,
        action_taken="INSTALLED_AS_REPLACEMENT",
        previous_status=old_rep_status,
        new_status="INSTALLED",
        project_id=ticket.project_id,
        recorded_by=current_user.id,
        remarks=f"Installed replacing defective serial {orig_sn.serial_number}",
    )
    db.add(h2)

    # 4. Create Replacement record
    replacement = Replacement(
        ticket_id=ticket.id,
        original_serial_id=orig_sn.id,
        replacement_serial_id=rep_sn.id,
        replacement_reason=payload.replacement_reason.strip(),
        replacement_date=payload.replacement_date,
        replaced_by=emp.id,
    )
    db.add(replacement)
    db.flush()

    # 5. If warranty record exists, update active serial and log REPLACEMENT event
    if ticket.warranty_record_id:
        w_rec = db.get(WarrantyRecord, ticket.warranty_record_id)
        if w_rec:
            w_rec.serial_number_id = rep_sn.id
        event = WarrantyEvent(
            warranty_record_id=ticket.warranty_record_id,
            event_type="REPLACEMENT",
            description=f"Component serial {orig_sn.serial_number} replaced by {rep_sn.serial_number}. Reason: {payload.replacement_reason}",
            recorded_by=current_user.id,
        )
        db.add(event)

    db.commit()
    db.refresh(replacement)

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="COMPONENT_REPLACEMENT",
        entity_name="SERVICE_TICKET",
        entity_id=ticket.id,
        details={
            "original_serial": orig_sn.serial_number,
            "replacement_serial": rep_sn.serial_number,
        },
    )
    db.commit()

    return APIResponse(
        message=f"Defective component '{orig_sn.serial_number}' successfully replaced with '{rep_sn.serial_number}'",
        data=ReplacementResponse(
            id=replacement.id,
            ticket_id=replacement.ticket_id,
            original_serial_id=replacement.original_serial_id,
            original_serial_number=orig_sn.serial_number,
            replacement_serial_id=replacement.replacement_serial_id,
            replacement_serial_number=rep_sn.serial_number,
            replacement_reason=replacement.replacement_reason,
            replacement_date=replacement.replacement_date,
            replaced_by=replacement.replaced_by,
            replacer_name=emp.user.full_name if emp.user else None,
            created_at=replacement.created_at,
        ),
    )


# ==========================================
# 6. SERVICE TICKET CONFIRMATIONS
# ==========================================

@router.post("/service-tickets/{id}/confirm", response_model=APIResponse[ServiceTicketConfirmationResponse], status_code=status.HTTP_201_CREATED)
def confirm_service_ticket_resolution(
    id: int,
    payload: ServiceTicketConfirmationCreate,
    current_user: User = Depends(require_service_access),
    db: Session = Depends(get_db),
):
    ticket = db.get(ServiceTicket, id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Service ticket not found")

    existing_conf = db.execute(select(ServiceTicketConfirmation).where(ServiceTicketConfirmation.ticket_id == ticket.id)).scalar_one_or_none()
    if existing_conf:
        raise HTTPException(status_code=400, detail="Service ticket has already been confirmed")

    conf = ServiceTicketConfirmation(
        ticket_id=ticket.id,
        customer_id=ticket.customer_id,
        resolution_confirmed=payload.resolution_confirmed,
        customer_rating=payload.customer_rating,
        customer_feedback=payload.customer_feedback,
        confirmation_channel=payload.confirmation_channel,
    )
    db.add(conf)

    if payload.resolution_confirmed:
        ticket.status = "RESOLVED"

    db.commit()
    db.refresh(conf)

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="SERVICE_TICKET_CONFIRMED",
        entity_name="SERVICE_TICKET",
        entity_id=ticket.id,
        details={"rating": payload.customer_rating, "confirmed": payload.resolution_confirmed},
    )
    db.commit()

    return APIResponse(
        message="Service ticket resolution confirmed successfully",
        data=ServiceTicketConfirmationResponse(
            id=conf.id,
            ticket_id=conf.ticket_id,
            customer_id=conf.customer_id,
            resolution_confirmed=conf.resolution_confirmed,
            customer_rating=conf.customer_rating,
            customer_feedback=conf.customer_feedback,
            confirmed_at=conf.confirmed_at,
            confirmation_channel=conf.confirmation_channel,
            created_at=conf.created_at,
        ),
    )


# ==========================================
# 8. SERVICE TICKET SLA METRICS & VISITS
# ==========================================

PRIORITY_SLA_HOURS = {
    "CRITICAL": 24.0,
    "HIGH": 48.0,
    "MEDIUM": 72.0,
    "LOW": 120.0,
}


@router.get("/warranty/sla-metrics", response_model=APIResponse[ServiceTicketSLAMetrics])
def get_service_sla_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed SLA metrics for service and warranty operations.
    Calculates aging buckets, approaching deadlines, overdue tickets, and resolution metrics.
    """
    now = datetime.now(timezone.utc)

    # 1. Open Tickets
    open_stmt = select(ServiceTicket).where(
        ServiceTicket.status.in_(["OPEN", "ASSIGNED", "IN_PROGRESS"])
    )
    open_tickets = db.execute(open_stmt).scalars().all()

    aging_buckets = {
        "< 24h": 0,
        "24h - 48h": 0,
        "48h - 72h": 0,
        "> 72h": 0,
    }
    approaching_count = 0
    overdue_count = 0

    for t in open_tickets:
        created_time = t.created_at if t.created_at.tzinfo else t.created_at.replace(tzinfo=timezone.utc)
        age_hours = (now - created_time).total_seconds() / 3600.0
        sla_target = PRIORITY_SLA_HOURS.get(str(t.priority).upper(), 72.0)

        # Aging bucket
        if age_hours < 24.0:
            aging_buckets["< 24h"] += 1
        elif age_hours < 48.0:
            aging_buckets["24h - 48h"] += 1
        elif age_hours < 72.0:
            aging_buckets["48h - 72h"] += 1
        else:
            aging_buckets["> 72h"] += 1

        # Overdue or approaching
        if age_hours > sla_target:
            overdue_count += 1
        elif (sla_target - 6.0) <= age_hours <= sla_target:
            approaching_count += 1

    # 2. Resolved Tickets
    resolved_stmt = select(ServiceTicket).where(
        ServiceTicket.status.in_(["RESOLVED", "CLOSED"])
    )
    resolved_tickets = db.execute(resolved_stmt).scalars().all()

    met_sla_count = 0
    total_res_hours = 0.0

    for t in resolved_tickets:
        c_time = t.created_at if t.created_at.tzinfo else t.created_at.replace(tzinfo=timezone.utc)
        u_time = t.updated_at if t.updated_at.tzinfo else t.updated_at.replace(tzinfo=timezone.utc)
        res_hours = max(0.0, (u_time - c_time).total_seconds() / 3600.0)
        sla_target = PRIORITY_SLA_HOURS.get(str(t.priority).upper(), 72.0)
        total_res_hours += res_hours

        if res_hours <= sla_target:
            met_sla_count += 1

    total_resolved = len(resolved_tickets)
    sla_compliance_pct = round((met_sla_count / total_resolved * 100.0), 1) if total_resolved > 0 else 100.0
    avg_res_hours = round(total_res_hours / total_resolved, 1) if total_resolved > 0 else None

    # 3. Monthly Resolution Trend (Last 6 months)
    monthly_trend_stmt = (
        select(
            func.to_char(ServiceTicket.created_at, "YYYY-MM").label("month"),
            func.count(ServiceTicket.id).label("total"),
            func.count(case((ServiceTicket.status.in_(["RESOLVED", "CLOSED"]), 1))).label("resolved"),
        )
        .group_by(func.to_char(ServiceTicket.created_at, "YYYY-MM"))
        .order_by(func.to_char(ServiceTicket.created_at, "YYYY-MM").desc())
        .limit(6)
    )
    trend_rows = db.execute(monthly_trend_stmt).all()
    resolution_trend = [
        {"month": r[0] or "N/A", "opened": int(r[1] or 0), "resolved": int(r[2] or 0)}
        for r in reversed(trend_rows)
    ]

    metrics = ServiceTicketSLAMetrics(
        total_open_tickets=len(open_tickets),
        open_tickets_by_sla_aging=aging_buckets,
        approaching_deadline_count=approaching_count,
        overdue_response_count=overdue_count,
        sla_compliance_percentage=sla_compliance_pct,
        average_resolution_hours=avg_res_hours,
        resolution_trend=resolution_trend,
    )

    return APIResponse(
        success=True,
        message="Service SLA metrics retrieved successfully",
        data=metrics,
    )


@router.get("/service-visits", response_model=APIResponse[dict])
def list_service_visits(
    technician_id: Optional[int] = Query(None),
    ticket_id: Optional[int] = Query(None),
    visit_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List service visits.
    If current user is FIELD_TECHNICIAN, results are scoped to their assigned visits.
    """
    query = (
        select(ServiceVisit)
        .options(
            selectinload(ServiceVisit.technician).selectinload(Employee.user),
            selectinload(ServiceVisit.ticket).selectinload(ServiceTicket.customer),
            selectinload(ServiceVisit.ticket).selectinload(ServiceTicket.project),
        )
    )

    if current_user.role and current_user.role.slug == SystemRole.FIELD_TECHNICIAN:
        emp = db.execute(select(Employee).where(Employee.user_id == current_user.id)).scalar_one_or_none()
        if emp:
            query = query.where(ServiceVisit.technician_id == emp.id)
        else:
            return APIResponse(message="No assigned visits found", data={"items": [], "total": 0})
    elif technician_id:
        query = query.where(ServiceVisit.technician_id == technician_id)

    if ticket_id:
        query = query.where(ServiceVisit.ticket_id == ticket_id)
    if visit_status:
        query = query.where(ServiceVisit.visit_status == visit_status.strip().upper())

    visits = db.execute(query.order_by(ServiceVisit.scheduled_date.asc())).scalars().all()

    items = []
    for v in visits:
        items.append({
            "id": v.id,
            "ticket_id": v.ticket_id,
            "ticket_number": v.ticket.ticket_number if v.ticket else None,
            "issue_category": v.ticket.issue_category if v.ticket else None,
            "priority": v.ticket.priority if v.ticket else "MEDIUM",
            "ticket_status": v.ticket.status if v.ticket else None,
            "customer_name": v.ticket.customer.full_name if v.ticket and v.ticket.customer else None,
            "customer_phone": v.ticket.customer.phone if v.ticket and v.ticket.customer else None,
            "site_address": v.ticket.project.site_address if v.ticket and v.ticket.project else None,
            "project_code": v.ticket.project.project_code if v.ticket and v.ticket.project else None,
            "technician_id": v.technician_id,
            "technician_name": v.technician.full_name if v.technician else None,
            "visit_number": v.visit_number,
            "scheduled_date": v.scheduled_date,
            "visit_status": v.visit_status,
            "actual_start": v.actual_start,
            "actual_end": v.actual_end,
            "findings": v.findings,
            "action_taken": v.action_taken,
            "parts_replaced": v.parts_replaced,
            "customer_present_name": v.customer_present_name,
            "created_at": v.created_at,
        })

    return APIResponse(
        success=True,
        message="Service visits retrieved successfully",
        data={"items": items, "total": len(items)},
    )
