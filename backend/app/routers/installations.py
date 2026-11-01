from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_, desc
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date, timezone
from decimal import Decimal
import math

from app.database import get_db
from app.models.auth import User, Role, Employee
from app.models.workflow import AuditLog
from app.models.crm import Customer, Product
from app.models.projects import Project, ProjectBomItem
from app.models.inventory import SerialNumber, SerialNumberHistory
from app.models.installations import (
    InstallationSchedule,
    InstallationScheduleTechnician,
    Installation,
    InstallationChecklist,
    InstallationPhoto,
    TechnicianWorklog,
    InstallationTest,
    MaterialConsumption,
    CustomerAcceptance,
)
from app.schemas.installations import (
    ScheduleTechnicianCreate,
    ScheduleTechnicianResponse,
    InstallationScheduleCreate,
    InstallationScheduleStatusUpdate,
    InstallationScheduleResponse,
    InstallationChecklistCreate,
    InstallationChecklistUpdate,
    InstallationChecklistResponse,
    TechnicianWorklogCreate,
    TechnicianWorklogResponse,
    InstallationTestCreate,
    InstallationTestResponse,
    MaterialConsumptionCreate,
    MaterialConsumptionResponse,
    CustomerAcceptanceCreate,
    CustomerAcceptanceResponse,
    InstallationCreate,
    InstallationStatusUpdate,
    InstallationResponse,
    InstallationDetailResponse,
    VALID_SCHEDULE_STATUSES,
    VALID_INSTALLATION_STATUSES,
    VALID_CHECKLIST_CATEGORIES,
    VALID_TEST_NAMES,
)
from app.schemas import APIResponse
from app.dependencies.auth import get_current_user, get_user_permissions
from app.utils.roles import SystemRole

router = APIRouter(tags=["Installation Management & Technical Commissioning"])


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


def require_installation_read_access(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role and current_user.role.slug in {
        SystemRole.SUPER_ADMIN,
        SystemRole.DIRECTOR,
        SystemRole.TECHNICAL_MANAGER,
        SystemRole.FIELD_TECHNICIAN,
        SystemRole.SERVICE_WARRANTY,
        SystemRole.FINANCE_ACCOUNTS,
        SystemRole.WAREHOUSE_PROCUREMENT,
        SystemRole.SALES,
        SystemRole.CUSTOMER,
    }:
        return current_user
    raise HTTPException(status_code=403, detail="Unauthorized to view installations")


def require_technician_or_manager(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role and current_user.role.slug in {
        SystemRole.SUPER_ADMIN,
        SystemRole.DIRECTOR,
        SystemRole.TECHNICAL_MANAGER,
        SystemRole.FIELD_TECHNICIAN,
    }:
        return current_user
    raise HTTPException(status_code=403, detail="Only installation managers and field technicians may perform this action")


def require_customer_or_manager(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role and current_user.role.slug in {
        SystemRole.SUPER_ADMIN,
        SystemRole.DIRECTOR,
        SystemRole.TECHNICAL_MANAGER,
        SystemRole.CUSTOMER,
    }:
        return current_user
    raise HTTPException(status_code=403, detail="Unauthorized to submit customer acceptance sign-off")


def _get_emp_name(emp: Optional[Employee]) -> Optional[str]:
    if not emp:
        return None
    if getattr(emp, "user", None) and getattr(emp.user, "full_name", None):
        return emp.user.full_name
    return emp.employee_code or f"EMP-{emp.id}"


# ==========================================
# 1. INSTALLATION SCHEDULES
# ==========================================

@router.get("/installation-schedules", response_model=APIResponse[dict])
@router.get("/installations/schedules", response_model=APIResponse[dict])
def list_installation_schedules(
    project_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(require_installation_read_access),
    db: Session = Depends(get_db),
):
    """
    List scheduled installation jobs with team assignments.
    """
    query = (
        select(InstallationSchedule)
        .options(
            selectinload(InstallationSchedule.project).selectinload(Project.customer),
            selectinload(InstallationSchedule.creator),
            selectinload(InstallationSchedule.technicians)
            .selectinload(InstallationScheduleTechnician.employee)
            .selectinload(Employee.user),
        )
    )

    if project_id:
        query = query.where(InstallationSchedule.project_id == project_id)
    if status_filter:
        query = query.where(InstallationSchedule.status == status_filter.strip().upper())

    # Field Technician Assignment Scoping
    if current_user.role and current_user.role.slug == SystemRole.FIELD_TECHNICIAN:
        emp = db.execute(select(Employee).where(Employee.user_id == current_user.id)).scalar_one_or_none()
        if emp:
            query = query.where(
                InstallationSchedule.technicians.any(InstallationScheduleTechnician.employee_id == emp.id)
            )
        else:
            return APIResponse(message="No assigned schedules found", data={"items": [], "total": 0})

    schedules = db.execute(query.order_by(InstallationSchedule.scheduled_start_date.desc())).scalars().all()

    items = []
    for s in schedules:
        tech_list = [
            ScheduleTechnicianResponse(
                id=t.id,
                schedule_id=t.schedule_id,
                employee_id=t.employee_id,
                employee_name=_get_emp_name(t.employee),
                role_in_team=t.role_in_team,
                assigned_at=t.assigned_at,
            )
            for t in (s.technicians or [])
        ]

        items.append(
            InstallationScheduleResponse(
                id=s.id,
                project_id=s.project_id,
                project_code=s.project.project_code if s.project else None,
                customer_name=s.project.customer.full_name if s.project and s.project.customer else None,
                scheduled_start_date=s.scheduled_start_date,
                scheduled_end_date=s.scheduled_end_date,
                actual_start_date=s.actual_start_date,
                actual_end_date=s.actual_end_date,
                status=s.status,
                notes=s.notes,
                created_by=s.created_by,
                creator_name=s.creator.full_name if s.creator else None,
                technicians_count=len(tech_list),
                technicians=tech_list,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
        )

    return APIResponse(message="Installation schedules retrieved", data={"items": items, "total": len(items)})


@router.post("/installation-schedules", response_model=APIResponse[InstallationScheduleResponse], status_code=status.HTTP_201_CREATED)
@router.post("/installations/schedules", response_model=APIResponse[InstallationScheduleResponse], status_code=status.HTTP_201_CREATED)
def create_installation_schedule(
    payload: InstallationScheduleCreate,
    current_user: User = Depends(require_technician_or_manager),
    db: Session = Depends(get_db),
):
    """
    Schedule an installation team for a project and assign lead/assistant technicians.
    """
    project = db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if payload.scheduled_end_date < payload.scheduled_start_date:
        raise HTTPException(status_code=400, detail="scheduled_end_date cannot be earlier than scheduled_start_date")

    schedule = InstallationSchedule(
        project_id=project.id,
        scheduled_start_date=payload.scheduled_start_date,
        scheduled_end_date=payload.scheduled_end_date,
        status="SCHEDULED",
        notes=payload.notes,
        created_by=current_user.id,
    )
    db.add(schedule)
    db.flush()

    for t in payload.technicians:
        emp = db.get(Employee, t.employee_id)
        if not emp:
            raise HTTPException(status_code=404, detail=f"Employee ID {t.employee_id} not found")
        tech_rel = InstallationScheduleTechnician(
            schedule_id=schedule.id,
            employee_id=emp.id,
            role_in_team=t.role_in_team,
        )
        db.add(tech_rel)

    db.commit()
    db.refresh(schedule)

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="SCHEDULE_INSTALLATION",
        entity_name="INSTALLATION_SCHEDULE",
        entity_id=schedule.id,
        details={"project_code": project.project_code, "team_size": len(payload.technicians)},
    )
    db.commit()

    return APIResponse(
        message="Installation scheduled successfully",
        data=_build_schedule_response(db, schedule.id),
    )


@router.patch("/installation-schedules/{schedule_id}/status", response_model=APIResponse[InstallationScheduleResponse])
@router.patch("/installations/schedules/{schedule_id}/status", response_model=APIResponse[InstallationScheduleResponse])
def update_installation_schedule_status(
    schedule_id: int,
    payload: InstallationScheduleStatusUpdate,
    current_user: User = Depends(require_technician_or_manager),
    db: Session = Depends(get_db),
):
    schedule = db.get(InstallationSchedule, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    target = payload.status.strip().upper()
    if target not in VALID_SCHEDULE_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid schedule status '{target}'")

    schedule.status = target
    if payload.actual_start_date:
        schedule.actual_start_date = payload.actual_start_date
    if payload.actual_end_date:
        schedule.actual_end_date = payload.actual_end_date
    if payload.notes:
        schedule.notes = payload.notes

    db.commit()
    return APIResponse(message=f"Schedule status updated to '{target}'", data=_build_schedule_response(db, schedule.id))


# ==========================================
# 2. INSTALLATIONS MAIN LIFECYCLE
# ==========================================

@router.get("/installations", response_model=APIResponse[dict])
def list_installations(
    project_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(require_installation_read_access),
    db: Session = Depends(get_db),
):
    query = (
        select(Installation)
        .options(
            selectinload(Installation.project).selectinload(Project.customer),
            selectinload(Installation.lead_technician).selectinload(Employee.user),
            selectinload(Installation.customer_acceptance),
        )
    )

    if project_id:
        query = query.where(Installation.project_id == project_id)
    if status_filter:
        query = query.where(Installation.status == status_filter.strip().upper())

    # Customer Data Scoping
    is_customer = current_user.role and current_user.role.slug == SystemRole.CUSTOMER
    if is_customer:
        cust = db.execute(select(Customer).where(Customer.user_id == current_user.id)).scalar_one_or_none()
        if not cust:
            return APIResponse(message="No installations found", data={"items": [], "total": 0})
        if project_id:
            proj = db.get(Project, project_id)
            if not proj or proj.customer_id != cust.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only access installations associated with your own customer account",
                )
        query = query.join(Installation.project).where(Project.customer_id == cust.id)

    # Field Technician Assignment Scoping
    if current_user.role and current_user.role.slug == SystemRole.FIELD_TECHNICIAN:
        emp = db.execute(select(Employee).where(Employee.user_id == current_user.id)).scalar_one_or_none()
        if emp:
            query = query.where(
                or_(
                    Installation.lead_technician_id == emp.id,
                    Installation.schedule.has(InstallationSchedule.technicians.any(InstallationScheduleTechnician.employee_id == emp.id))
                )
            )
        else:
            return APIResponse(message="No assigned installations found", data={"items": [], "total": 0})

    installs = db.execute(query.order_by(Installation.installation_date.desc())).scalars().all()

    items = []
    for inst in installs:
        items.append(
            InstallationResponse(
                id=inst.id,
                project_id=inst.project_id,
                project_code=inst.project.project_code if inst.project else None,
                customer_name=inst.project.customer.full_name if inst.project and inst.project.customer else None,
                site_address=inst.project.site_address if inst.project else None,
                schedule_id=inst.schedule_id,
                lead_technician_id=inst.lead_technician_id,
                lead_technician_name=_get_emp_name(inst.lead_technician),
                system_capacity_kw=inst.system_capacity_kw,
                inverter_make_model=inst.inverter_make_model,
                total_panels_installed=inst.total_panels_installed,
                structure_type=inst.structure_type,
                installation_date=inst.installation_date,
                commissioning_date=inst.commissioning_date,
                status=inst.status,
                technician_notes=None if is_customer else inst.technician_notes,
                is_commissioned=inst.customer_acceptance is not None and inst.customer_acceptance.is_accepted,
                created_at=inst.created_at,
                updated_at=inst.updated_at,
            )
        )

    return APIResponse(message="Installations retrieved", data={"items": items, "total": len(items)})


@router.get("/installations/{installation_id}", response_model=APIResponse[InstallationDetailResponse])
def get_installation_detail(
    installation_id: int,
    current_user: User = Depends(require_installation_read_access),
    db: Session = Depends(get_db),
):
    inst = (
        db.execute(
            select(Installation)
            .options(selectinload(Installation.project))
            .where(Installation.id == installation_id)
        )
        .scalars()
        .first()
    )
    if not inst:
        raise HTTPException(status_code=404, detail="Installation record not found")

    is_customer = current_user.role and current_user.role.slug == SystemRole.CUSTOMER
    if is_customer:
        cust = db.execute(select(Customer).where(Customer.user_id == current_user.id)).scalar_one_or_none()
        if not cust or not inst.project or inst.project.customer_id != cust.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access installation details for your own projects",
            )

    return APIResponse(message="Installation details retrieved", data=_build_installation_detail(db, installation_id, is_customer=is_customer))


@router.post("/installations", response_model=APIResponse[InstallationDetailResponse], status_code=status.HTTP_201_CREATED)
def create_installation(
    payload: InstallationCreate,
    current_user: User = Depends(require_technician_or_manager),
    db: Session = Depends(get_db),
):
    """
    Create a project installation record and advance project status to INSTALLATION.
    """
    project = db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    existing = db.execute(select(Installation).where(Installation.project_id == payload.project_id)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail=f"Installation record already exists for project '{project.project_code}'")

    lead_emp = db.get(Employee, payload.lead_technician_id)
    if not lead_emp:
        raise HTTPException(status_code=404, detail="Lead technician employee record not found")

    installation = Installation(
        project_id=project.id,
        schedule_id=payload.schedule_id,
        lead_technician_id=lead_emp.id,
        system_capacity_kw=payload.system_capacity_kw,
        inverter_make_model=payload.inverter_make_model,
        total_panels_installed=payload.total_panels_installed,
        structure_type=payload.structure_type,
        installation_date=payload.installation_date,
        status="IN_PROGRESS",
        technician_notes=payload.technician_notes,
    )
    db.add(installation)

    # Transition Project status to INSTALLATION / IN_PROGRESS
    if project.status in {"COMMITTED", "DISPATCHED", "PROCUREMENT", "INITIATED"}:
        project.status = "INSTALLATION"

    db.commit()
    db.refresh(installation)

    # Seed standard default checklists automatically
    _seed_default_checklists(db, installation.id)

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="INSTALLATION_START",
        entity_name="INSTALLATION",
        entity_id=installation.id,
        details={"project_code": project.project_code, "capacity_kw": float(payload.system_capacity_kw)},
    )
    db.commit()

    return APIResponse(
        message=f"Installation record for project '{project.project_code}' initialized successfully",
        data=_build_installation_detail(db, installation.id),
    )


@router.patch("/installations/{installation_id}/status", response_model=APIResponse[InstallationResponse])
def update_installation_status(
    installation_id: int,
    payload: InstallationStatusUpdate,
    current_user: User = Depends(require_technician_or_manager),
    db: Session = Depends(get_db),
):
    inst = db.get(Installation, installation_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Installation not found")

    target = payload.status.strip().upper()
    if target not in VALID_INSTALLATION_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid installation status '{target}'")

    inst.status = target
    if payload.commissioning_date:
        inst.commissioning_date = payload.commissioning_date
    if payload.technician_notes:
        inst.technician_notes = payload.technician_notes

    db.commit()
    return APIResponse(message=f"Installation status updated to '{target}'", data=_build_installation_summary(db, inst.id))


# ==========================================
# 3. CHECKLISTS
# ==========================================

@router.get("/installations/{installation_id}/checklists", response_model=APIResponse[List[InstallationChecklistResponse]])
def get_installation_checklists(
    installation_id: int,
    current_user: User = Depends(require_installation_read_access),
    db: Session = Depends(get_db),
):
    inst = (
        db.execute(
            select(Installation)
            .options(selectinload(Installation.project))
            .where(Installation.id == installation_id)
        )
        .scalars()
        .first()
    )
    if not inst:
        raise HTTPException(status_code=404, detail="Installation record not found")

    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        cust = db.execute(select(Customer).where(Customer.user_id == current_user.id)).scalar_one_or_none()
        if not cust or not inst.project or inst.project.customer_id != cust.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access checklists for your own projects",
            )

    items = db.execute(
        select(InstallationChecklist)
        .options(selectinload(InstallationChecklist.verifier))
        .where(InstallationChecklist.installation_id == installation_id)
        .order_by(InstallationChecklist.id.asc())
    ).scalars().all()

    resp = [
        InstallationChecklistResponse(
            id=it.id,
            installation_id=it.installation_id,
            checklist_item=it.checklist_item,
            category=it.category,
            is_checked=it.is_checked,
            remarks=it.remarks,
            verified_by=it.verified_by,
            verifier_name=it.verifier.full_name if it.verifier else None,
            verified_at=it.verified_at,
            created_at=it.created_at,
        )
        for it in items
    ]
    return APIResponse(message="Checklists retrieved", data=resp)


@router.post("/installations/{installation_id}/checklists", response_model=APIResponse[InstallationChecklistResponse], status_code=status.HTTP_201_CREATED)
def add_checklist_item(
    installation_id: int,
    payload: InstallationChecklistCreate,
    current_user: User = Depends(require_technician_or_manager),
    db: Session = Depends(get_db),
):
    inst = db.get(Installation, installation_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Installation not found")

    item = InstallationChecklist(
        installation_id=inst.id,
        checklist_item=payload.checklist_item.strip(),
        category=payload.category.strip().upper(),
        is_checked=payload.is_checked,
        remarks=payload.remarks,
        verified_by=current_user.id if payload.is_checked else None,
        verified_at=datetime.now(timezone.utc) if payload.is_checked else None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return APIResponse(
        message="Checklist item added",
        data=InstallationChecklistResponse(
            id=item.id,
            installation_id=item.installation_id,
            checklist_item=item.checklist_item,
            category=item.category,
            is_checked=item.is_checked,
            remarks=item.remarks,
            verified_by=item.verified_by,
            verifier_name=current_user.full_name if item.verified_by else None,
            verified_at=item.verified_at,
            created_at=item.created_at,
        ),
    )


@router.patch("/installations/checklists/{checklist_id}", response_model=APIResponse[InstallationChecklistResponse])
def update_checklist_item(
    checklist_id: int,
    payload: InstallationChecklistUpdate,
    current_user: User = Depends(require_technician_or_manager),
    db: Session = Depends(get_db),
):
    item = db.get(InstallationChecklist, checklist_id)
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    item.is_checked = payload.is_checked
    if payload.remarks is not None:
        item.remarks = payload.remarks

    if payload.is_checked:
        item.verified_by = current_user.id
        item.verified_at = datetime.now(timezone.utc)
    else:
        item.verified_by = None
        item.verified_at = None

    db.commit()
    db.refresh(item)

    verifier = db.get(User, item.verified_by) if item.verified_by else None
    return APIResponse(
        message="Checklist item verified",
        data=InstallationChecklistResponse(
            id=item.id,
            installation_id=item.installation_id,
            checklist_item=item.checklist_item,
            category=item.category,
            is_checked=item.is_checked,
            remarks=item.remarks,
            verified_by=item.verified_by,
            verifier_name=verifier.full_name if verifier else None,
            verified_at=item.verified_at,
            created_at=item.created_at,
        ),
    )


# ==========================================
# 4. WORKLOGS
# ==========================================

@router.post("/installations/{installation_id}/worklogs", response_model=APIResponse[TechnicianWorklogResponse], status_code=status.HTTP_201_CREATED)
def submit_technician_worklog(
    installation_id: int,
    payload: TechnicianWorklogCreate,
    current_user: User = Depends(require_technician_or_manager),
    db: Session = Depends(get_db),
):
    inst = db.get(Installation, installation_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Installation not found")

    emp = db.get(Employee, payload.employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    worklog = TechnicianWorklog(
        installation_id=inst.id,
        employee_id=emp.id,
        work_date=payload.work_date,
        hours_worked=payload.hours_worked,
        work_description=payload.work_description.strip(),
    )
    db.add(worklog)
    db.commit()
    db.refresh(worklog)

    return APIResponse(
        message="Worklog logged successfully",
        data=TechnicianWorklogResponse(
            id=worklog.id,
            installation_id=worklog.installation_id,
            employee_id=worklog.employee_id,
            employee_name=_get_emp_name(emp),
            work_date=worklog.work_date,
            hours_worked=worklog.hours_worked,
            work_description=worklog.work_description,
            approved_by=None,
            approver_name=None,
            approved_at=None,
            created_at=worklog.created_at,
        ),
    )


@router.post("/installations/worklogs/{worklog_id}/approve", response_model=APIResponse[TechnicianWorklogResponse])
def approve_technician_worklog(
    worklog_id: int,
    current_user: User = Depends(require_technician_or_manager),
    db: Session = Depends(get_db),
):
    worklog = db.get(TechnicianWorklog, worklog_id)
    if not worklog:
        raise HTTPException(status_code=404, detail="Worklog not found")

    worklog.approved_by = current_user.id
    worklog.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(worklog)

    emp = db.get(Employee, worklog.employee_id)
    return APIResponse(
        message="Worklog approved successfully",
        data=TechnicianWorklogResponse(
            id=worklog.id,
            installation_id=worklog.installation_id,
            employee_id=worklog.employee_id,
            employee_name=_get_emp_name(emp),
            work_date=worklog.work_date,
            hours_worked=worklog.hours_worked,
            work_description=worklog.work_description,
            approved_by=worklog.approved_by,
            approver_name=current_user.full_name,
            approved_at=worklog.approved_at,
            created_at=worklog.created_at,
        ),
    )


# ==========================================
# 5. ELECTRICAL TESTING & COMMISSIONING
# ==========================================

@router.post("/installations/{installation_id}/tests", response_model=APIResponse[InstallationTestResponse], status_code=status.HTTP_201_CREATED)
def record_installation_test(
    installation_id: int,
    payload: InstallationTestCreate,
    current_user: User = Depends(require_technician_or_manager),
    db: Session = Depends(get_db),
):
    inst = db.get(Installation, installation_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Installation not found")

    tester = db.get(Employee, payload.tested_by)
    if not tester:
        raise HTTPException(status_code=404, detail="Tester employee record not found")

    test = InstallationTest(
        installation_id=inst.id,
        test_name=payload.test_name.strip().upper(),
        standard_value=payload.standard_value,
        measured_value=payload.measured_value.strip(),
        unit_of_measure=payload.unit_of_measure.strip(),
        is_passed=payload.is_passed,
        tested_by=tester.id,
        test_date=payload.test_date,
        remarks=payload.remarks,
    )
    db.add(test)
    db.commit()
    db.refresh(test)

    return APIResponse(
        message=f"Test '{test.test_name}' recorded successfully",
        data=InstallationTestResponse(
            id=test.id,
            installation_id=test.installation_id,
            test_name=test.test_name,
            standard_value=test.standard_value,
            measured_value=test.measured_value,
            unit_of_measure=test.unit_of_measure,
            is_passed=test.is_passed,
            tested_by=test.tested_by,
            tester_name=_get_emp_name(tester),
            test_date=test.test_date,
            remarks=test.remarks,
            created_at=test.created_at,
        ),
    )


# ==========================================
# 6. MATERIAL CONSUMPTION & RECONCILIATION
# ==========================================

@router.post("/installations/{installation_id}/materials", response_model=APIResponse[MaterialConsumptionResponse], status_code=status.HTTP_201_CREATED)
def record_material_consumption(
    installation_id: int,
    payload: MaterialConsumptionCreate,
    current_user: User = Depends(require_technician_or_manager),
    db: Session = Depends(get_db),
):
    """
    Record material consumption on-site with full concurrency safety and ledger integrity.
    - Locks installation and project BOM records with FOR UPDATE
    - Validates dispatched vs consumed BOM quantities
    - Validates serial numbers: status must be DISPATCHED, belongs to project and product
    - Prevents duplicate consumption retry
    - Atomically updates ProjectBomItem.installed_quantity and transitions SerialNumber status to 'INSTALLED'.
    """
    inst = db.execute(
        select(Installation).where(Installation.id == installation_id).with_for_update()
    ).scalar_one_or_none()
    if not inst:
        raise HTTPException(status_code=404, detail="Installation not found")

    product = db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # If serial number is supplied, validate serialized component state and row-lock
    serial_obj = None
    if payload.serial_number_id:
        serial_obj = db.execute(
            select(SerialNumber).where(SerialNumber.id == payload.serial_number_id).with_for_update()
        ).scalar_one_or_none()
        if not serial_obj:
            raise HTTPException(status_code=404, detail="Serial number record not found")

        # Validate product match
        if serial_obj.product_id != payload.product_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Serial number '{serial_obj.serial_number}' belongs to product ID {serial_obj.product_id}, which does not match payload product ID {payload.product_id}.",
            )

        # Validate project match (if allocated to a project, must match current installation project)
        if serial_obj.project_id is not None and serial_obj.project_id != inst.project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Serial number '{serial_obj.serial_number}' is allocated to project ID {serial_obj.project_id}, not installation project ID {inst.project_id}.",
            )

        # Prevent duplicate consumption on retry / idempotency guard
        existing_cons = db.execute(
            select(MaterialConsumption).where(MaterialConsumption.serial_number_id == serial_obj.id)
        ).scalar_one_or_none()
        if existing_cons:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Serial number '{serial_obj.serial_number}' has already been consumed (Consumption record ID: {existing_cons.id}).",
            )

        # Validate status must be DISPATCHED
        if serial_obj.status != "DISPATCHED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Serial number '{serial_obj.serial_number}' must be in 'DISPATCHED' status to be installed on-site (Current status: '{serial_obj.status}').",
            )

    # Row-lock ProjectBomItem to serialize concurrent consumption updates
    bom_item = db.execute(
        select(ProjectBomItem).where(
            ProjectBomItem.project_id == inst.project_id,
            ProjectBomItem.product_id == payload.product_id,
        ).with_for_update()
    ).scalar_one_or_none()

    # Validate consumption against remaining dispatched quantity if not marked as extra material
    if not payload.is_extra_material:
        if not bom_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.name}' is not in the project BOM. Mark as extra material if this is an off-BOM consumption.",
            )
        remaining_dispatched = bom_item.dispatched_quantity - bom_item.installed_quantity
        if payload.quantity_consumed > remaining_dispatched:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Consumed quantity ({payload.quantity_consumed}) exceeds remaining dispatched quantity ({remaining_dispatched}). "
                    f"Dispatched: {bom_item.dispatched_quantity}, Already installed: {bom_item.installed_quantity}. "
                    f"Mark as extra material if additional consumption is required."
                ),
            )

    if serial_obj:
        prev = serial_obj.status
        serial_obj.status = "INSTALLED"
        serial_obj.project_id = inst.project_id

        hist = SerialNumberHistory(
            serial_number_id=serial_obj.id,
            previous_status=prev,
            new_status="INSTALLED",
            project_id=inst.project_id,
            action_taken="INSTALLED_ON_SITE",
            recorded_by=current_user.id,
            remarks=f"Installed via installation ID {inst.id}",
        )
        db.add(hist)

    if bom_item:
        bom_item.installed_quantity += payload.quantity_consumed

    consumption = MaterialConsumption(
        installation_id=inst.id,
        product_id=product.id,
        serial_number_id=payload.serial_number_id,
        quantity_consumed=payload.quantity_consumed,
        unit_of_measure=payload.unit_of_measure,
        is_extra_material=payload.is_extra_material,
        remarks=payload.remarks,
    )
    db.add(consumption)
    db.commit()
    db.refresh(consumption)

    return APIResponse(
        message=f"Recorded consumption of {payload.quantity_consumed} {payload.unit_of_measure} for '{product.name}'",
        data=MaterialConsumptionResponse(
            id=consumption.id,
            installation_id=consumption.installation_id,
            product_id=consumption.product_id,
            product_code=product.product_code,
            product_name=product.name,
            serial_number_id=consumption.serial_number_id,
            serial_number=serial_obj.serial_number if serial_obj else None,
            quantity_consumed=consumption.quantity_consumed,
            unit_of_measure=consumption.unit_of_measure,
            is_extra_material=consumption.is_extra_material,
            remarks=consumption.remarks,
            created_at=consumption.created_at,
        ),
    )


# ==========================================
# 7. CUSTOMER ACCEPTANCE SIGN-OFF
# ==========================================

@router.post("/installations/{installation_id}/customer-acceptance", response_model=APIResponse[CustomerAcceptanceResponse], status_code=status.HTTP_201_CREATED)
def record_customer_acceptance(
    installation_id: int,
    payload: CustomerAcceptanceCreate,
    current_user: User = Depends(require_customer_or_manager),
    db: Session = Depends(get_db),
):
    """
    Formal sign-off of the solar installation by the customer.
    Prerequisites:
    1. Valid existing Installation and Project records.
    2. Customer ownership verification (authenticated customer owns project).
    3. Project and Installation in valid operational status for handover.
    4. All mandatory installation checklists completed and verified.
    5. All electrical safety and commissioning tests passed.
    6. Concurrency-safe duplicate prevention.
    """
    inst = db.execute(
        select(Installation)
        .options(
            selectinload(Installation.project).selectinload(Project.customer),
            selectinload(Installation.checklists),
            selectinload(Installation.tests),
            selectinload(Installation.customer_acceptance),
        )
        .where(or_(Installation.id == installation_id, Installation.project_id == installation_id))
        .with_for_update()
    ).scalars().first()

    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Installation record not found. Installation must be initialized before customer acceptance sign-off.",
        )

    project = inst.project
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated project not found")

    # Customer scope and user-link integrity verification
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        cust = db.execute(select(Customer).where(Customer.user_id == current_user.id)).scalar_one_or_none()
        if not cust or project.customer_id != cust.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only submit handover acceptance for your own customer project",
            )

    # Prevent duplicate acceptance
    existing_accept = inst.customer_acceptance or db.execute(
        select(CustomerAcceptance).where(CustomerAcceptance.installation_id == inst.id)
    ).scalar_one_or_none()

    if existing_accept or inst.status == "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer acceptance has already been recorded for this installation",
        )

    # Project operational state verification
    if project.status in ("INITIATED", "PLANNING", "SURVEY", "CANCELLED", "ON_HOLD"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot record customer acceptance: project is in invalid operational status '{project.status}'",
        )

    if inst.status in ("FAILED_INSPECTION", "CANCELLED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot record customer acceptance: installation is in invalid status '{inst.status}'",
        )

    # Mandatory checklists completion verification
    checklists = inst.checklists or []
    if not checklists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot record customer acceptance: installation checklists have not been initialized.",
        )
    incomplete_checklists = [c.checklist_item for c in checklists if not c.is_checked]
    if incomplete_checklists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot record customer acceptance: {len(incomplete_checklists)} installation checklist items are incomplete.",
        )

    # Mandatory electrical safety and commissioning tests verification
    tests = inst.tests or []
    if not tests:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot record customer acceptance: electrical commissioning tests have not been recorded.",
        )
    failed_tests = [t.test_name for t in tests if not t.is_passed]
    if failed_tests:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot record customer acceptance: electrical safety tests failed ({', '.join(failed_tests)}).",
        )

    notes = payload.satisfaction_notes or payload.acceptance_notes or "Installation verified and accepted by customer"
    rating = payload.rating_overall if payload.rating_overall is not None else 5

    acceptance = CustomerAcceptance(
        installation_id=inst.id,
        project_id=project.id,
        customer_id=project.customer_id,
        acceptance_date=payload.acceptance_date,
        rating_overall=rating,
        satisfaction_notes=notes,
        is_accepted=payload.is_accepted,
    )
    db.add(acceptance)

    if payload.is_accepted:
        inst.status = "COMPLETED"
        inst.commissioning_date = payload.acceptance_date
        project.status = "COMPLETED"
        project.actual_completion_date = payload.acceptance_date

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="CUSTOMER_ACCEPTANCE",
        entity_name="CUSTOMER_ACCEPTANCE",
        entity_id=inst.id,
        details={
            "project_code": project.project_code,
            "rating": rating,
            "is_accepted": payload.is_accepted,
        },
    )
    db.commit()
    db.refresh(acceptance)

    cust = db.get(Customer, project.customer_id)
    return APIResponse(
        message=f"Customer acceptance sign-off recorded successfully for project '{project.project_code}'",
        data=CustomerAcceptanceResponse(
            id=acceptance.id,
            installation_id=acceptance.installation_id,
            project_id=acceptance.project_id,
            customer_id=acceptance.customer_id,
            customer_name=cust.full_name if cust else None,
            acceptance_date=acceptance.acceptance_date,
            rating_overall=acceptance.rating_overall,
            satisfaction_notes=acceptance.satisfaction_notes,
            is_accepted=acceptance.is_accepted,
            created_at=acceptance.created_at,
        ),
    )


# ==========================================
# INTERNAL UTILS
# ==========================================

def _seed_default_checklists(db: Session, installation_id: int):
    defaults = [
        ("Verify roof structural integrity and rafter mounting", "CIVIL"),
        ("Check solar module clamp torque and tilt orientation", "MECHANICAL"),
        ("String cable routing with UV-resistant conduit and cable ties", "ELECTRICAL"),
        ("Inverter AC/DC isolator and surge protection device (SPD) installation", "ELECTRICAL"),
        ("Dedicated chemical earthing pit connection with earth resistance < 5 Ohms", "SAFETY"),
        ("Danger warning boards, dual earth strip and schematic labeling", "SAFETY"),
        ("Anti-islanding and grid synchronization test", "COMMISSIONING"),
    ]
    for item, cat in defaults:
        cl = InstallationChecklist(
            installation_id=installation_id,
            checklist_item=item,
            category=cat,
            is_checked=False,
        )
        db.add(cl)
    db.commit()


def _build_schedule_response(db: Session, schedule_id: int) -> InstallationScheduleResponse:
    s = (
        db.execute(
            select(InstallationSchedule)
            .options(
                selectinload(InstallationSchedule.project).selectinload(Project.customer),
                selectinload(InstallationSchedule.creator),
                selectinload(InstallationSchedule.technicians)
                .selectinload(InstallationScheduleTechnician.employee)
                .selectinload(Employee.user),
            )
            .where(InstallationSchedule.id == schedule_id)
        )
        .scalars()
        .first()
    )
    tech_list = [
        ScheduleTechnicianResponse(
            id=t.id,
            schedule_id=t.schedule_id,
            employee_id=t.employee_id,
            employee_name=_get_emp_name(t.employee),
            role_in_team=t.role_in_team,
            assigned_at=t.assigned_at,
        )
        for t in (s.technicians or [])
    ]
    return InstallationScheduleResponse(
        id=s.id,
        project_id=s.project_id,
        project_code=s.project.project_code if s.project else None,
        customer_name=s.project.customer.full_name if s.project and s.project.customer else None,
        scheduled_start_date=s.scheduled_start_date,
        scheduled_end_date=s.scheduled_end_date,
        actual_start_date=s.actual_start_date,
        actual_end_date=s.actual_end_date,
        status=s.status,
        notes=s.notes,
        created_by=s.created_by,
        creator_name=s.creator.full_name if s.creator else None,
        technicians_count=len(tech_list),
        technicians=tech_list,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


def _build_installation_summary(db: Session, installation_id: int, is_customer: bool = False) -> InstallationResponse:
    inst = (
        db.execute(
            select(Installation)
            .options(
                selectinload(Installation.project).selectinload(Project.customer),
                selectinload(Installation.lead_technician).selectinload(Employee.user),
                selectinload(Installation.customer_acceptance),
            )
            .where(Installation.id == installation_id)
        )
        .scalars()
        .first()
    )
    return InstallationResponse(
        id=inst.id,
        project_id=inst.project_id,
        project_code=inst.project.project_code if inst.project else None,
        customer_name=inst.project.customer.full_name if inst.project and inst.project.customer else None,
        site_address=inst.project.site_address if inst.project else None,
        schedule_id=inst.schedule_id,
        lead_technician_id=inst.lead_technician_id,
        lead_technician_name=_get_emp_name(inst.lead_technician),
        system_capacity_kw=inst.system_capacity_kw,
        inverter_make_model=inst.inverter_make_model,
        total_panels_installed=inst.total_panels_installed,
        structure_type=inst.structure_type,
        installation_date=inst.installation_date,
        commissioning_date=inst.commissioning_date,
        status=inst.status,
        technician_notes=None if is_customer else inst.technician_notes,
        is_commissioned=inst.customer_acceptance is not None and inst.customer_acceptance.is_accepted,
        created_at=inst.created_at,
        updated_at=inst.updated_at,
    )


def _build_installation_detail(db: Session, installation_id: int, is_customer: bool = False) -> InstallationDetailResponse:
    inst = (
        db.execute(
            select(Installation)
            .options(
                selectinload(Installation.project).selectinload(Project.customer),
                selectinload(Installation.lead_technician).selectinload(Employee.user),
                selectinload(Installation.checklists).selectinload(InstallationChecklist.verifier),
                selectinload(Installation.tests).selectinload(InstallationTest.tester).selectinload(Employee.user),
                selectinload(Installation.worklogs).selectinload(TechnicianWorklog.employee).selectinload(Employee.user),
                selectinload(Installation.worklogs).selectinload(TechnicianWorklog.approver),
                selectinload(Installation.materials).selectinload(MaterialConsumption.product),
                selectinload(Installation.materials).selectinload(MaterialConsumption.serial),
                selectinload(Installation.customer_acceptance).selectinload(CustomerAcceptance.customer),
            )
            .where(Installation.id == installation_id)
        )
        .scalars()
        .first()
    )
    if not inst:
        raise HTTPException(status_code=404, detail="Installation record not found")

    summary = _build_installation_summary(db, installation_id, is_customer=is_customer)

    checklists_resp = [
        InstallationChecklistResponse(
            id=c.id,
            installation_id=c.installation_id,
            checklist_item=c.checklist_item,
            category=c.category,
            is_checked=c.is_checked,
            remarks=c.remarks,
            verified_by=c.verified_by,
            verifier_name=c.verifier.full_name if c.verifier else None,
            verified_at=c.verified_at,
            created_at=c.created_at,
        )
        for c in (inst.checklists or [])
    ]

    tests_resp = [
        InstallationTestResponse(
            id=t.id,
            installation_id=t.installation_id,
            test_name=t.test_name,
            standard_value=t.standard_value,
            measured_value=t.measured_value,
            unit_of_measure=t.unit_of_measure,
            is_passed=t.is_passed,
            tested_by=t.tested_by,
            tester_name=_get_emp_name(t.tester),
            test_date=t.test_date,
            remarks=t.remarks,
            created_at=t.created_at,
        )
        for t in (inst.tests or [])
    ]

    worklogs_resp = [] if is_customer else [
        TechnicianWorklogResponse(
            id=w.id,
            installation_id=w.installation_id,
            employee_id=w.employee_id,
            employee_name=_get_emp_name(w.employee),
            work_date=w.work_date,
            hours_worked=w.hours_worked,
            work_description=w.work_description,
            approved_by=w.approved_by,
            approver_name=w.approver.full_name if w.approver else None,
            approved_at=w.approved_at,
            created_at=w.created_at,
        )
        for w in (inst.worklogs or [])
    ]

    materials_resp = [
        MaterialConsumptionResponse(
            id=m.id,
            installation_id=m.installation_id,
            product_id=m.product_id,
            product_code=m.product.product_code if m.product else None,
            product_name=m.product.name if m.product else None,
            serial_number_id=m.serial_number_id,
            serial_number=m.serial.serial_number if m.serial else None,
            quantity_consumed=m.quantity_consumed,
            unit_of_measure=m.unit_of_measure,
            is_extra_material=m.is_extra_material,
            remarks=m.remarks,
            created_at=m.created_at,
        )
        for m in (inst.materials or [])
    ]

    acceptance_resp = None
    if inst.customer_acceptance:
        ca = inst.customer_acceptance
        acceptance_resp = CustomerAcceptanceResponse(
            id=ca.id,
            installation_id=ca.installation_id,
            project_id=ca.project_id,
            customer_id=ca.customer_id,
            customer_name=ca.customer.full_name if ca.customer else None,
            acceptance_date=ca.acceptance_date,
            rating_overall=ca.rating_overall,
            satisfaction_notes=ca.satisfaction_notes,
            is_accepted=ca.is_accepted,
            created_at=ca.created_at,
        )

    return InstallationDetailResponse(
        **summary.model_dump(),
        checklists=checklists_resp,
        tests=tests_resp,
        worklogs=worklogs_resp,
        materials=materials_resp,
        customer_acceptance=acceptance_resp,
    )
