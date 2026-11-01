from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from datetime import date, datetime, timedelta
import uuid
import logging

from app.database import get_db
from app.models.auth import User, Employee
from app.models.crm import Customer, Quotation, QuotationItem, Product
from app.models.projects import Order, Project, ProjectBomItem, ProjectNote
from app.models.workflow import Task, AuditLog, Notification
from app.dependencies.auth import get_current_user, require_permissions
from app.utils.roles import SystemRole
from app.schemas import APIResponse
from app.schemas.orders import OrderCustomerSummary, OrderResponse, OrderQuotationSummary, OrderProjectSummary, OrderPaymentSummary
from app.schemas.bom import ProjectBomItemResponse
from app.schemas.projects import (
    ProjectHandoverRequest,
    ProjectUpdateRequest,
    ProjectNoteCreateRequest,
    ProjectNoteResponse,
    ProjectTaskResponse,
    ProjectResponse,
    ProjectListResponse,
    VALID_PROJECT_STATUSES,
    VALID_NOTE_TYPES,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects"])


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
        entity_name="PROJECT",
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


def _build_project_bom_item_response(it: ProjectBomItem) -> ProjectBomItemResponse:
    prod = it.product
    planned = float(it.planned_quantity)
    unit_cost = float(it.unit_cost_snapshot)
    total_cost = planned * unit_cost
    return ProjectBomItemResponse(
        id=it.id,
        project_id=it.project_id,
        product_id=it.product_id,
        product_code=prod.product_code if prod else "UNKNOWN",
        product_name=prod.name if prod else "Unknown Product",
        item_category=it.item_category,
        brand=prod.brand if prod else None,
        model_number=prod.model_number if prod else None,
        unit_of_measure=prod.unit_of_measure if prod else "NOS",
        planned_quantity=planned,
        allocated_quantity=float(it.allocated_quantity),
        dispatched_quantity=float(it.dispatched_quantity),
        installed_quantity=float(it.installed_quantity),
        unit_cost_snapshot=unit_cost,
        total_planned_cost=total_cost,
        created_at=it.created_at,
        updated_at=it.updated_at,
    )


def _build_project_response(project: Project, db: Session, current_user: Optional[User] = None) -> ProjectResponse:
    # 1. Customer
    cust_summary = None
    if project.customer:
        cust_summary = OrderCustomerSummary(
            id=project.customer.id,
            full_name=project.customer.full_name,
            phone=project.customer.phone,
            email=project.customer.email,
            city=project.customer.city,
            state=project.customer.state,
        )

    # 2. Order summary
    order_summary = None
    if project.order:
        quo_summary = None
        if project.order.quotation:
            quo_summary = OrderQuotationSummary(
                id=project.order.quotation.id,
                quotation_number=project.order.quotation.quotation_number,
                system_type=project.order.quotation.system_type,
                capacity_kw=Decimal(str(project.order.quotation.capacity_kw)),
                gross_amount=Decimal(str(project.order.quotation.gross_amount)),
                net_payable_amount=Decimal(str(project.order.quotation.net_payable_amount)),
                status=project.order.quotation.status,
            )

        order_summary = OrderResponse(
            id=project.order.id,
            order_number=project.order.order_number,
            quotation_id=project.order.quotation_id,
            customer_id=project.order.customer_id,
            order_date=project.order.order_date,
            total_amount=Decimal(str(project.order.total_amount)),
            advance_paid=Decimal(str(project.order.advance_paid)),
            balance_amount=Decimal(str(project.order.balance_amount)),
            status=project.order.status,
            created_by=project.order.created_by,
            created_at=project.order.created_at,
            updated_at=project.order.updated_at,
            customer=cust_summary,
            quotation=quo_summary,
            payments=[],
        )

    # 3. BOM items
    bom_items = [
        _build_project_bom_item_response(it)
        for it in (project.bom_items or [])
    ]

    # 4. Notes (Customer isolation: hide internal notes if user is CUSTOMER)
    is_customer = current_user and current_user.role and current_user.role.slug == SystemRole.CUSTOMER
    notes_list = []
    for n in (project.notes or []):
        if is_customer and n.is_internal:
            continue
        notes_list.append(
            ProjectNoteResponse(
                id=n.id,
                project_id=n.project_id,
                note_type=n.note_type,
                content=n.note_text,
                is_internal=n.is_internal,
                author_id=n.author_id,
                author_name=n.author.full_name if hasattr(n, "author") and n.author else None,
                created_at=n.created_at,
            )
        )

    # 5. Tasks
    tasks_data = db.execute(
        select(Task).where(Task.project_id == project.id).order_by(Task.created_at.asc())
    ).scalars().all()

    tasks_list = [
        ProjectTaskResponse(
            id=t.id,
            task_code=t.task_code,
            title=t.title,
            task_type=t.task_type,
            priority=t.priority,
            status=t.status,
            due_date=t.due_date,
            created_at=t.created_at,
        )
        for t in tasks_data
    ]

    pm_name = None
    if project.project_manager:
        if hasattr(project.project_manager, "user") and project.project_manager.user:
            pm_name = project.project_manager.user.full_name
        elif hasattr(project.project_manager, "full_name"):
            pm_name = project.project_manager.full_name

    return ProjectResponse(
        id=project.id,
        project_code=project.project_code,
        order_id=project.order_id,
        customer_id=project.customer_id,
        project_manager_id=project.project_manager_id,
        project_manager_name=pm_name,
        system_capacity_kw=Decimal(str(project.system_capacity_kw)),
        system_type=project.system_type,
        site_address=project.site_address,
        planned_start_date=project.planned_start_date,
        planned_completion_date=project.planned_completion_date,
        actual_completion_date=project.actual_completion_date,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        customer=cust_summary,
        order=order_summary,
        bom_items=bom_items,
        notes=notes_list,
        tasks=tasks_list,
    )


# ==========================================
# PROJECT HANDOVER & MANAGEMENT ENDPOINTS
# ==========================================

@router.post("/orders/{order_id}/handover", response_model=APIResponse[ProjectResponse], status_code=status.HTTP_201_CREATED)
def handover_order_to_project(
    order_id: int,
    payload: ProjectHandoverRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("projects.create")),
):
    """
    Sales-to-Operations Handover: Initialize a Project from an eligible Order.
    Requires 'projects.create' permission (held by SUPER_ADMIN, TECHNICAL_MANAGER).
    Enforces that:
    1. Order must exist and not be CANCELLED.
    2. Order must be eligible (if in PENDING_ADVANCE, advance_paid must be > 0 or confirmed).
    3. Exactly one Project per Order (concurrency-protected via with_for_update and unique index).
    4. Accepted quotation line items form the base project BOM lines atomically.
    5. Standard execution setup tasks are seeded in the tasks table.
    """
    # 1. Row-level lock on the target Order
    order = db.execute(
        select(Order)
        .options(
            selectinload(Order.customer),
            selectinload(Order.quotation).selectinload(Quotation.items).selectinload(QuotationItem.product),
            selectinload(Order.quotation).selectinload(Quotation.survey),
        )
        .where(Order.id == order_id)
        .with_for_update()
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found.",
        )

    # 2. Check if a project already exists for this order
    existing_project = db.execute(
        select(Project).where(Project.order_id == order.id)
    ).scalar_one_or_none()

    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A project ('{existing_project.project_code}') has already been initialized for order '{order.order_number}'. At most one project per order is permitted.",
        )

    # 3. Eligibility verification
    if order.status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot perform operations handover for a CANCELLED order.",
        )

    if order.status == "PENDING_ADVANCE" and order.advance_paid <= Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order '{order.order_number}' is in 'PENDING_ADVANCE' status with zero advance payment recorded. An advance payment must be recorded or order confirmed prior to operations handover.",
        )

    quotation = order.quotation
    if not quotation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order '{order.order_number}' is missing associated quotation details.",
        )

    # 4. Resolve site address
    resolved_address = payload.site_address
    if not resolved_address or not resolved_address.strip():
        if quotation.survey and quotation.survey.site_address:
            resolved_address = quotation.survey.site_address
        elif order.customer and order.customer.address:
            resolved_address = f"{order.customer.address}, {order.customer.city or ''} {order.customer.state or ''} {order.customer.pincode or ''}".strip()
        else:
            resolved_address = "Site address pending customer verification"

    # 5. Resolve timeline dates
    start_date = payload.planned_start_date or date.today()
    comp_date = payload.planned_completion_date or (start_date + timedelta(days=30))
    if comp_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Planned completion date cannot be earlier than planned start date.",
        )

    # 6. Verify project manager if provided
    if payload.project_manager_id:
        pm = db.execute(
            select(Employee).where(Employee.id == payload.project_manager_id)
        ).scalar_one_or_none()
        if not pm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project manager employee with ID {payload.project_manager_id} not found.",
            )

    # 7. Generate collision-resistant project code
    proj_code = f"PRJ-{date.today().year}-{uuid.uuid4().hex[:6].upper()}"

    project = Project(
        project_code=proj_code,
        order_id=order.id,
        customer_id=order.customer_id,
        project_manager_id=payload.project_manager_id,
        system_capacity_kw=Decimal(str(quotation.capacity_kw)),
        system_type=quotation.system_type,
        site_address=resolved_address.strip(),
        planned_start_date=start_date,
        planned_completion_date=comp_date,
        status="INITIATED",
    )
    db.add(project)

    try:
        db.flush()  # Allocate project.id and enforce unique constraints
    except IntegrityError as exc:
        db.rollback()
        err_msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)
        if "order_id" in err_msg.lower() or "unique" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A project has already been initialized for order '{order.order_number}'. Duplicate project rejected.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error while creating project: {err_msg}",
        )

    # 8. Transfer quotation items into project_bom_items atomically
    # Group items by product_id to aggregate planned quantity and respect (project_id, product_id) unique constraint
    grouped_items: Dict[int, Dict] = {}
    for it in (quotation.items or []):
        if not it.product_id:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Quotation item '{it.item_description}' is missing a valid product reference. Cannot transfer to BOM.",
            )

        if it.product_id not in grouped_items:
            cat = it.product.category if it.product and it.product.category else "MISC"
            grouped_items[it.product_id] = {
                "product_id": it.product_id,
                "item_category": cat,
                "quantity": Decimal(str(it.quantity)),
                "unit_cost_snapshot": Decimal(str(it.unit_price)),
            }
        else:
            grouped_items[it.product_id]["quantity"] += Decimal(str(it.quantity))

    for p_id, item_info in grouped_items.items():
        bom_item = ProjectBomItem(
            project_id=project.id,
            product_id=p_id,
            item_category=item_info["item_category"],
            planned_quantity=item_info["quantity"],
            allocated_quantity=Decimal("0.00"),
            dispatched_quantity=Decimal("0.00"),
            installed_quantity=Decimal("0.00"),
            unit_cost_snapshot=item_info["unit_cost_snapshot"],
        )
        db.add(bom_item)

    # 9. Create standard initial setup tasks for operations
    task1 = Task(
        task_code=f"TSK-{uuid.uuid4().hex[:6].upper()}",
        project_id=project.id,
        title="Site Preparation & Structural Verification",
        description=f"Verify rooftop structural readiness and cable routing for {quotation.capacity_kw} kW {quotation.system_type} installation at {resolved_address}.",
        task_type="INSTALLATION",
        priority="MEDIUM",
        status="PENDING",
        due_date=start_date + timedelta(days=7),
        created_by=current_user.id,
    )
    task2 = Task(
        task_code=f"TSK-{uuid.uuid4().hex[:6].upper()}",
        project_id=project.id,
        title="Procurement & Inventory Allocation",
        description=f"Allocate warehouse stock and verify equipment availability for project {project.project_code}.",
        task_type="PROCUREMENT",
        priority="HIGH",
        status="PENDING",
        due_date=start_date + timedelta(days=14),
        created_by=current_user.id,
    )
    db.add(task1)
    db.add(task2)

    # 10. Initial notes if provided
    if payload.initial_notes and payload.initial_notes.strip():
        note = ProjectNote(
            project_id=project.id,
            author_id=current_user.id,
            note_type="GENERAL",
            note_text=payload.initial_notes.strip(),
            is_internal=True,
        )
        db.add(note)

    # 11. Update Order status to PROCESSING if currently CONFIRMED or PENDING_ADVANCE
    if order.status in ("CONFIRMED", "PENDING_ADVANCE"):
        order.status = "PROCESSING"

    # 12. Record audit log
    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="PROJECT_HANDOVER",
        entity_id=project.id,
        details={
            "project_code": project.project_code,
            "order_id": order.id,
            "order_number": order.order_number,
            "customer_id": order.customer_id,
            "system_capacity_kw": float(project.system_capacity_kw),
            "system_type": project.system_type,
            "bom_items_transferred": len(grouped_items),
        },
    )

    # 13. Notify project manager if assigned
    if project.project_manager_id and project.project_manager and project.project_manager.user_id:
        _send_notification(
            db=db,
            user_id=project.project_manager.user_id,
            title="Project Handover Assigned",
            message=f"You have been assigned as Project Manager for newly initialized project {project.project_code}.",
            notification_type="TASK",
        )

    db.commit()

    # Re-fetch project with relationships
    loaded_project = db.execute(
        select(Project)
        .options(
            selectinload(Project.customer),
            selectinload(Project.order).selectinload(Order.quotation),
            selectinload(Project.project_manager),
            selectinload(Project.bom_items).selectinload(ProjectBomItem.product),
            selectinload(Project.notes).selectinload(ProjectNote.author),
        )
        .where(Project.id == project.id)
    ).scalar_one()

    return APIResponse(
        success=True,
        message=f"Operations handover complete. Project '{loaded_project.project_code}' initialized with {len(grouped_items)} base BOM items.",
        data=_build_project_response(loaded_project, db, current_user),
    )


@router.get("", response_model=APIResponse[ProjectListResponse])
def list_projects(
    search: Optional[str] = Query(None, description="Search by project code, customer name, or address"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    status: Optional[str] = Query(None, description="Filter by project status"),
    system_type: Optional[str] = Query(None, description="Filter by system type (ON_GRID, OFF_GRID, HYBRID)"),
    project_manager_id: Optional[int] = Query(None, description="Filter by project manager employee ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("projects.read")),
):
    """
    List solar rooftop execution projects with filters and pagination.
    Applies strict customer isolation: Customer accounts can only view their own projects.
    """
    stmt = (
        select(Project)
        .options(
            selectinload(Project.customer),
            selectinload(Project.order).selectinload(Order.quotation),
            selectinload(Project.project_manager),
            selectinload(Project.bom_items).selectinload(ProjectBomItem.product),
            selectinload(Project.notes).selectinload(ProjectNote.author),
        )
    )

    # Customer isolation
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        customer = _get_customer_for_user(current_user, db)
        if not customer:
            return APIResponse(
                success=True,
                message="No projects found",
                data=ProjectListResponse(items=[], total=0, page=page, limit=limit, pages=0),
            )
        stmt = stmt.where(Project.customer_id == customer.id)
    elif customer_id:
        stmt = stmt.where(Project.customer_id == customer_id)

    if status:
        clean_status = status.strip().upper()
        stmt = stmt.where(Project.status == clean_status)

    if system_type:
        clean_st = system_type.strip().upper()
        stmt = stmt.where(Project.system_type == clean_st)

    if project_manager_id:
        stmt = stmt.where(Project.project_manager_id == project_manager_id)

    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.join(Project.customer).where(
            or_(
                Project.project_code.ilike(term),
                Project.site_address.ilike(term),
                Customer.full_name.ilike(term),
                Customer.phone.ilike(term),
            )
        )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar() or 0

    offset = (page - 1) * limit
    projects = db.execute(
        stmt.order_by(Project.created_at.desc()).offset(offset).limit(limit)
    ).scalars().all()

    pages = (total + limit - 1) // limit if total > 0 else 0
    items = [_build_project_response(p, db, current_user) for p in projects]

    return APIResponse(
        success=True,
        message=f"Retrieved {len(items)} projects.",
        data=ProjectListResponse(items=items, total=total, page=page, limit=limit, pages=pages),
    )


@router.get("/{id}", response_model=APIResponse[ProjectResponse])
def get_project(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("projects.read")),
):
    """
    Retrieve full project details including Order, Customer, BOM items, Notes, and Tasks.
    Applies customer ownership verification and internal note masking for customers.
    """
    project = db.execute(
        select(Project)
        .options(
            selectinload(Project.customer),
            selectinload(Project.order).selectinload(Order.quotation),
            selectinload(Project.project_manager),
            selectinload(Project.bom_items).selectinload(ProjectBomItem.product),
            selectinload(Project.notes).selectinload(ProjectNote.author),
        )
        .where(Project.id == id)
    ).scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {id} not found.",
        )

    # Customer isolation
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        customer = _get_customer_for_user(current_user, db)
        if not customer or project.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access projects associated with your own customer account.",
            )

    return APIResponse(
        success=True,
        message="Project details retrieved successfully.",
        data=_build_project_response(project, db, current_user),
    )


@router.put("/{id}", response_model=APIResponse[ProjectResponse])
def update_project(
    id: int,
    payload: ProjectUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("projects.update")),
):
    """
    Update project execution details (status, dates, assigned project manager, site address).
    Requires 'projects.update' permission (held by SUPER_ADMIN, TECHNICAL_MANAGER).
    """
    project = db.execute(
        select(Project)
        .options(
            selectinload(Project.customer),
            selectinload(Project.order).selectinload(Order.quotation),
            selectinload(Project.project_manager),
            selectinload(Project.bom_items).selectinload(ProjectBomItem.product),
            selectinload(Project.notes).selectinload(ProjectNote.author),
        )
        .where(Project.id == id)
        .with_for_update()
    ).scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {id} not found.",
        )

    changes = {}

    if payload.status:
        target_status = payload.status.strip().upper()
        if target_status not in VALID_PROJECT_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid project status '{target_status}'. Permitted: {sorted(list(VALID_PROJECT_STATUSES))}",
            )
        changes["status"] = {"old": project.status, "new": target_status}
        project.status = target_status

    if payload.project_manager_id is not None:
        if payload.project_manager_id != project.project_manager_id:
            pm = db.execute(
                select(Employee).where(Employee.id == payload.project_manager_id)
            ).scalar_one_or_none()
            if not pm:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Employee with ID {payload.project_manager_id} not found.",
                )
            changes["project_manager_id"] = {"old": project.project_manager_id, "new": payload.project_manager_id}
            project.project_manager_id = payload.project_manager_id

    if payload.planned_start_date:
        project.planned_start_date = payload.planned_start_date

    if payload.planned_completion_date:
        if payload.planned_completion_date < project.planned_start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Planned completion date cannot be earlier than planned start date.",
            )
        project.planned_completion_date = payload.planned_completion_date

    if payload.actual_completion_date:
        if payload.actual_completion_date < project.planned_start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Actual completion date cannot be earlier than planned start date.",
            )
        project.actual_completion_date = payload.actual_completion_date

    if payload.site_address and payload.site_address.strip():
        project.site_address = payload.site_address.strip()

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="PROJECT_UPDATED",
        entity_id=project.id,
        details={"changes": changes},
    )

    db.commit()
    db.refresh(project)

    return APIResponse(
        success=True,
        message="Project details updated successfully.",
        data=_build_project_response(project, db, current_user),
    )


@router.post("/{id}/notes", response_model=APIResponse[ProjectNoteResponse], status_code=status.HTTP_201_CREATED)
def add_project_note(
    id: int,
    payload: ProjectNoteCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("projects.read")),
):
    """
    Add a technical, site, or general note to a Project.
    Customer accounts can only add non-internal notes to their own projects.
    Staff accounts can create internal or public notes.
    """
    project = db.execute(
        select(Project).where(Project.id == id)
    ).scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {id} not found.",
        )

    # Customer isolation
    is_customer = current_user.role and current_user.role.slug == SystemRole.CUSTOMER
    if is_customer:
        customer = _get_customer_for_user(current_user, db)
        if not customer or project.customer_id != customer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only add notes to your own projects.",
            )

    note_type = payload.note_type.strip().upper()
    if note_type not in VALID_NOTE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid note type '{note_type}'. Permitted: {sorted(list(VALID_NOTE_TYPES))}",
        )

    # Force customer notes to not be internal
    is_internal = False if is_customer else payload.is_internal

    note = ProjectNote(
        project_id=project.id,
        author_id=current_user.id,
        note_type=note_type,
        note_text=payload.content.strip(),
        is_internal=is_internal,
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="PROJECT_NOTE_ADDED",
        entity_id=project.id,
        details={"note_id": note.id, "note_type": note_type, "is_internal": is_internal},
    )

    return APIResponse(
        success=True,
        message="Project note added successfully.",
        data=ProjectNoteResponse(
            id=note.id,
            project_id=note.project_id,
            note_type=note.note_type,
            content=note.note_text,
            is_internal=note.is_internal,
            author_id=note.author_id,
            author_name=current_user.full_name,
            created_at=note.created_at,
        ),
    )
