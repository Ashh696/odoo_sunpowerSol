from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
import math

from app.database import get_db
from app.models.projects import BomTemplate, BomItem, ProjectBomItem, Project
from app.models.crm import Product
from app.models.auth import User
from app.models.workflow import AuditLog
from app.schemas.bom import (
    BomItemCreate,
    BomItemUpdate,
    BomItemResponse,
    BomTemplateCreate,
    BomTemplateUpdate,
    BomTemplateStatusUpdate,
    BomTemplateResponse,
    BomTemplateDetailResponse,
    BomTemplateListResponse,
    ProjectBomGenerateRequest,
    ProjectBomItemUpdate,
    ProjectBomItemResponse,
    ProjectBomListResponse,
    VALID_SYSTEM_TYPES,
)
from app.schemas import APIResponse
from app.dependencies.auth import get_current_user, get_user_permissions
from app.utils.roles import SystemRole

router = APIRouter(prefix="", tags=["Bill of Materials (BOM)"])


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


def require_bom_read_access(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure user has read permission for BOM templates and project BOMs.
    SUPER_ADMIN has universal access.
    CUSTOMER, FIELD_TECHNICIAN, SALES, and unauthorized roles are blocked.
    Other roles require 'bom.read'.
    """
    if current_user.role and current_user.role.slug == SystemRole.SUPER_ADMIN:
        return current_user

    if current_user.role and current_user.role.slug in (
        SystemRole.CUSTOMER,
        SystemRole.FIELD_TECHNICIAN,
        SystemRole.SALES,
        SystemRole.FINANCE_ACCOUNTS,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role privileges to access Bill of Materials",
        )

    user_perms = get_user_permissions(current_user)
    if "bom.read" in user_perms:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Missing required permission: bom.read",
    )


def require_bom_manage_access(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure user has management permission for BOM templates and project BOMs.
    SUPER_ADMIN and TECHNICAL_MANAGER have management access.
    DIRECTOR and WAREHOUSE_PROCUREMENT are read-only.
    All other roles are blocked.
    """
    if current_user.role and current_user.role.slug == SystemRole.SUPER_ADMIN:
        return current_user

    if current_user.role and current_user.role.slug in (
        SystemRole.CUSTOMER,
        SystemRole.FIELD_TECHNICIAN,
        SystemRole.SALES,
        SystemRole.FINANCE_ACCOUNTS,
        SystemRole.DIRECTOR,
        SystemRole.WAREHOUSE_PROCUREMENT,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role privileges to modify or manage Bill of Materials",
        )

    user_perms = get_user_permissions(current_user)
    if "bom.manage" in user_perms:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Missing required permission: bom.manage",
    )


def _build_bom_item_response(item: BomItem) -> BomItemResponse:
    p = item.product
    return BomItemResponse(
        id=item.id,
        bom_template_id=item.bom_template_id,
        product_id=item.product_id,
        product_code=p.product_code if p else None,
        product_name=p.name if p else None,
        brand=p.brand if p else None,
        model_number=p.model_number if p else None,
        wattage_or_capacity=p.wattage_or_capacity if p else None,
        item_category=item.item_category,
        default_quantity=float(item.default_quantity),
        unit_of_measure=item.unit_of_measure,
        is_mandatory=item.is_mandatory,
        unit_price=float(p.base_price) if p and p.base_price is not None else None,
        is_product_active=p.is_active if p else None,
        created_at=item.created_at,
    )


def _build_template_response(template: BomTemplate) -> BomTemplateResponse:
    item_cnt = len(template.items) if template.items else 0
    creator_name = template.creator.full_name if hasattr(template, "creator") and template.creator else None
    return BomTemplateResponse(
        id=template.id,
        template_name=template.template_name,
        system_type=template.system_type,
        capacity_kw=float(template.capacity_kw),
        description=template.description,
        is_active=template.is_active,
        created_by=template.created_by,
        creator_name=creator_name,
        item_count=item_cnt,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


def _build_template_detail_response(template: BomTemplate) -> BomTemplateDetailResponse:
    base = _build_template_response(template)
    items = [_build_bom_item_response(it) for it in template.items] if template.items else []
    return BomTemplateDetailResponse(
        **base.model_dump(),
        items=items,
    )


def _build_project_bom_item_response(item: ProjectBomItem) -> ProjectBomItemResponse:
    p = item.product
    planned = float(item.planned_quantity)
    unit_cost = float(item.unit_cost_snapshot)
    total_cost = planned * unit_cost
    return ProjectBomItemResponse(
        id=item.id,
        project_id=item.project_id,
        product_id=item.product_id,
        product_code=p.product_code if p else None,
        product_name=p.name if p else None,
        brand=p.brand if p else None,
        item_category=item.item_category,
        planned_quantity=planned,
        allocated_quantity=float(item.allocated_quantity),
        dispatched_quantity=float(item.dispatched_quantity),
        installed_quantity=float(item.installed_quantity),
        unit_cost_snapshot=unit_cost,
        total_planned_cost=total_cost,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


# ==========================================
# 1. BOM TEMPLATE ENDPOINTS
# ==========================================

@router.post("/bom/templates", response_model=APIResponse[BomTemplateDetailResponse], status_code=status.HTTP_201_CREATED)
def create_bom_template(
    payload: BomTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bom_manage_access),
):
    """
    Create a new master BOM template parameterized by system type and capacity.
    Optionally seeds initial components.
    """
    clean_name = payload.template_name.strip()

    # Pre-check template_name uniqueness
    existing = db.execute(
        select(BomTemplate).where(func.lower(BomTemplate.template_name) == clean_name.lower())
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"BOM template with name '{clean_name}' already exists",
        )

    # Validate items if provided
    seen_products = set()
    validated_items_data = []
    if payload.items:
        for it in payload.items:
            if it.product_id in seen_products:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Duplicate product ID {it.product_id} in template items",
                )
            seen_products.add(it.product_id)

            prod = db.execute(select(Product).where(Product.id == it.product_id)).scalar_one_or_none()
            if not prod:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {it.product_id} not found in catalog",
                )
            if not prod.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{prod.product_code}' is inactive and cannot be added to a new template",
                )

            uom = it.unit_of_measure.strip().upper() if it.unit_of_measure else prod.unit_of_measure
            if uom != prod.unit_of_measure.upper():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"UOM '{uom}' does not match product '{prod.product_code}' UOM '{prod.unit_of_measure}'",
                )

            cat = it.item_category.strip().upper() if it.item_category else prod.category
            validated_items_data.append((prod, cat, it.default_quantity, uom, it.is_mandatory))

    template = BomTemplate(
        template_name=clean_name,
        system_type=payload.system_type,
        capacity_kw=payload.capacity_kw,
        description=payload.description.strip() if payload.description else None,
        is_active=payload.is_active,
        created_by=current_user.id,
    )
    db.add(template)

    try:
        db.flush()  # Allocate template.id
        for prod, cat, qty, uom, is_mand in validated_items_data:
            item = BomItem(
                bom_template_id=template.id,
                product_id=prod.id,
                item_category=cat,
                default_quantity=qty,
                unit_of_measure=uom,
                is_mandatory=is_mand,
            )
            db.add(item)

        db.commit()
    except IntegrityError as exc:
        db.rollback()
        err_str = str(exc).lower()
        if "template_name" in err_str or "unique" in err_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"BOM template with name '{clean_name}' already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity conflict during template creation: {str(exc.orig) if hasattr(exc, 'orig') else str(exc)}",
        )

    _record_audit_log(
        db,
        user_id=current_user.id,
        action="CREATE",
        entity_name="BOM_TEMPLATE",
        entity_id=template.id,
        details={
            "template_name": template.template_name,
            "system_type": template.system_type,
            "capacity_kw": float(template.capacity_kw),
            "item_count": len(validated_items_data),
        },
    )
    db.commit()

    # Eager reload
    reloaded = db.execute(
        select(BomTemplate)
        .where(BomTemplate.id == template.id)
        .options(
            selectinload(BomTemplate.items).selectinload(BomItem.product),
        )
    ).scalar_one()

    return APIResponse(
        success=True,
        message=f"BOM template '{reloaded.template_name}' created successfully",
        data=_build_template_detail_response(reloaded),
    )


@router.get("/bom/templates", response_model=APIResponse[BomTemplateListResponse])
def list_bom_templates(
    search: Optional[str] = Query(None, description="Search by template name or description"),
    system_type: Optional[str] = Query(None, description="Filter by system type (ON_GRID, OFF_GRID, HYBRID)"),
    capacity_kw: Optional[float] = Query(None, description="Filter by capacity in kW"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bom_read_access),
):
    """
    List and search BOM master templates with system type, capacity, and status filters.
    """
    stmt = (
        select(BomTemplate)
        .options(
            selectinload(BomTemplate.items),
        )
    )

    if system_type:
        clean_st = system_type.strip().upper()
        if clean_st in VALID_SYSTEM_TYPES:
            stmt = stmt.where(BomTemplate.system_type == clean_st)

    if capacity_kw is not None:
        stmt = stmt.where(BomTemplate.capacity_kw == capacity_kw)

    if is_active is not None:
        stmt = stmt.where(BomTemplate.is_active == is_active)

    if search:
        term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(BomTemplate.template_name).like(term),
                func.lower(BomTemplate.description).like(term),
            )
        )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar() or 0

    stmt = stmt.order_by(BomTemplate.system_type.asc(), BomTemplate.capacity_kw.asc(), BomTemplate.template_name.asc())
    stmt = stmt.offset((page - 1) * limit).limit(limit)
    templates = db.execute(stmt).scalars().all()

    items = [_build_template_response(t) for t in templates]
    total_pages = math.ceil(total / limit) if total > 0 else 1

    return APIResponse(
        success=True,
        message="BOM templates retrieved successfully",
        data=BomTemplateListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        ),
    )


@router.get("/bom/templates/{template_id}", response_model=APIResponse[BomTemplateDetailResponse])
def get_bom_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bom_read_access),
):
    """
    Retrieve full details of a BOM template including all component lines and equipment specifications.
    """
    template = db.execute(
        select(BomTemplate)
        .where(BomTemplate.id == template_id)
        .options(
            selectinload(BomTemplate.items).selectinload(BomItem.product),
        )
    ).scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BOM template with ID {template_id} not found",
        )

    return APIResponse(
        success=True,
        message="BOM template details retrieved successfully",
        data=_build_template_detail_response(template),
    )


@router.put("/bom/templates/{template_id}", response_model=APIResponse[BomTemplateDetailResponse])
def update_bom_template(
    template_id: int,
    payload: BomTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bom_manage_access),
):
    """
    Update BOM template header metadata (name, system type, capacity, description).
    """
    template = db.execute(
        select(BomTemplate)
        .where(BomTemplate.id == template_id)
        .options(
            selectinload(BomTemplate.items).selectinload(BomItem.product),
        )
    ).scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BOM template with ID {template_id} not found",
        )

    # Check for name uniqueness conflict if name is changed
    if payload.template_name and payload.template_name.lower() != template.template_name.lower():
        conflict = db.execute(
            select(BomTemplate.id).where(
                func.lower(BomTemplate.template_name) == payload.template_name.lower(),
                BomTemplate.id != template.id,
            )
        ).scalar_one_or_none()
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"BOM template with name '{payload.template_name}' already exists",
            )
        template.template_name = payload.template_name

    if payload.system_type is not None:
        template.system_type = payload.system_type
    if payload.capacity_kw is not None:
        template.capacity_kw = payload.capacity_kw
    if payload.description is not None:
        template.description = payload.description.strip() if payload.description else None
    if payload.is_active is not None:
        template.is_active = payload.is_active

    template.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(template)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database update conflict: {str(exc.orig) if hasattr(exc, 'orig') else str(exc)}",
        )

    _record_audit_log(
        db,
        user_id=current_user.id,
        action="UPDATE",
        entity_name="BOM_TEMPLATE",
        entity_id=template.id,
        details={"template_name": template.template_name, "is_active": template.is_active},
    )
    db.commit()

    return APIResponse(
        success=True,
        message=f"BOM template '{template.template_name}' updated successfully",
        data=_build_template_detail_response(template),
    )


@router.patch("/bom/templates/{template_id}/status", response_model=APIResponse[BomTemplateResponse])
def update_bom_template_status(
    template_id: int,
    payload: BomTemplateStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bom_manage_access),
):
    """
    Activate or deactivate a BOM template. Inactive templates cannot be selected for new BOM generation.
    """
    template = db.execute(
        select(BomTemplate)
        .where(BomTemplate.id == template_id)
        .options(selectinload(BomTemplate.items))
    ).scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BOM template with ID {template_id} not found",
        )

    template.is_active = payload.is_active
    template.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(template)

    action_label = "ACTIVATE" if payload.is_active else "DEACTIVATE"
    _record_audit_log(
        db,
        user_id=current_user.id,
        action=action_label,
        entity_name="BOM_TEMPLATE",
        entity_id=template.id,
        details={"is_active": template.is_active},
    )
    db.commit()

    status_str = "activated" if template.is_active else "deactivated"
    return APIResponse(
        success=True,
        message=f"BOM template '{template.template_name}' has been {status_str}",
        data=_build_template_response(template),
    )


@router.post("/bom/templates/{template_id}/items", response_model=APIResponse[BomItemResponse], status_code=status.HTTP_201_CREATED)
def add_bom_template_item(
    template_id: int,
    payload: BomItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bom_manage_access),
):
    """
    Add a component product line item to an existing BOM template.
    Validates product active status, UOM, and duplicate prevention.
    """
    template = db.execute(select(BomTemplate).where(BomTemplate.id == template_id)).scalar_one_or_none()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BOM template with ID {template_id} not found",
        )

    # Validate product
    product = db.execute(select(Product).where(Product.id == payload.product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {payload.product_id} not found in catalog",
        )
    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product '{product.product_code}' is inactive and cannot be added to a template",
        )

    # Check for duplicate item in this template
    existing_item = db.execute(
        select(BomItem).where(
            BomItem.bom_template_id == template_id,
            BomItem.product_id == payload.product_id,
        )
    ).scalar_one_or_none()
    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product '{product.product_code}' already exists in template '{template.template_name}'",
        )

    uom = payload.unit_of_measure.strip().upper() if payload.unit_of_measure else product.unit_of_measure
    if uom != product.unit_of_measure.upper():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"UOM '{uom}' does not match product '{product.product_code}' UOM '{product.unit_of_measure}'",
        )

    category = payload.item_category.strip().upper() if payload.item_category else product.category

    item = BomItem(
        bom_template_id=template.id,
        product_id=product.id,
        item_category=category,
        default_quantity=payload.default_quantity,
        unit_of_measure=uom,
        is_mandatory=payload.is_mandatory,
    )
    db.add(item)

    try:
        db.commit()
        db.refresh(item)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate product conflict in template items",
        )

    _record_audit_log(
        db,
        user_id=current_user.id,
        action="ITEM_ADD",
        entity_name="BOM_TEMPLATE",
        entity_id=template.id,
        details={
            "product_code": product.product_code,
            "quantity": float(item.default_quantity),
            "item_id": item.id,
        },
    )
    db.commit()

    return APIResponse(
        success=True,
        message=f"Component '{product.product_code}' added to template",
        data=_build_bom_item_response(item),
    )


@router.put("/bom/templates/{template_id}/items/{item_id}", response_model=APIResponse[BomItemResponse])
def update_bom_template_item(
    template_id: int,
    item_id: int,
    payload: BomItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bom_manage_access),
):
    """
    Update default quantity, UOM, or mandatory flag of a template item.
    """
    item = db.execute(
        select(BomItem)
        .where(BomItem.id == item_id, BomItem.bom_template_id == template_id)
        .options(selectinload(BomItem.product))
    ).scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BOM item with ID {item_id} not found in template {template_id}",
        )

    if payload.default_quantity is not None:
        item.default_quantity = payload.default_quantity

    if payload.unit_of_measure is not None:
        clean_uom = payload.unit_of_measure.strip().upper()
        if item.product and clean_uom != item.product.unit_of_measure.upper():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"UOM '{clean_uom}' does not match product UOM '{item.product.unit_of_measure}'",
            )
        item.unit_of_measure = clean_uom

    if payload.item_category is not None:
        item.item_category = payload.item_category.strip().upper()

    if payload.is_mandatory is not None:
        item.is_mandatory = payload.is_mandatory

    db.commit()
    db.refresh(item)

    _record_audit_log(
        db,
        user_id=current_user.id,
        action="ITEM_UPDATE",
        entity_name="BOM_TEMPLATE",
        entity_id=template_id,
        details={"item_id": item.id, "default_quantity": float(item.default_quantity)},
    )
    db.commit()

    return APIResponse(
        success=True,
        message="Template component updated successfully",
        data=_build_bom_item_response(item),
    )


@router.delete("/bom/templates/{template_id}/items/{item_id}", response_model=APIResponse[dict])
def remove_bom_template_item(
    template_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bom_manage_access),
):
    """
    Remove a component line item from a template.
    Does not affect previously generated project BOMs or quotation snapshots.
    """
    item = db.execute(
        select(BomItem)
        .where(BomItem.id == item_id, BomItem.bom_template_id == template_id)
        .options(selectinload(BomItem.product))
    ).scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BOM item with ID {item_id} not found in template {template_id}",
        )

    prod_code = item.product.product_code if item.product else str(item.product_id)
    db.delete(item)
    db.commit()

    _record_audit_log(
        db,
        user_id=current_user.id,
        action="ITEM_REMOVE",
        entity_name="BOM_TEMPLATE",
        entity_id=template_id,
        details={"item_id": item_id, "product_code": prod_code},
    )
    db.commit()

    return APIResponse(
        success=True,
        message=f"Component '{prod_code}' removed from template",
        data={"deleted_item_id": item_id, "template_id": template_id},
    )


# ==========================================
# 2. PROJECT BOM ENDPOINTS
# ==========================================

@router.get("/projects/{project_id}/bom", response_model=APIResponse[ProjectBomListResponse])
def get_project_bom(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bom_read_access),
):
    """
    Retrieve project BOM lines including planned, allocated, dispatched, and installed quantities.
    """
    project = db.execute(select(Project).where(Project.id == project_id)).scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )

    stmt = (
        select(ProjectBomItem)
        .where(ProjectBomItem.project_id == project_id)
        .options(selectinload(ProjectBomItem.product))
        .order_by(ProjectBomItem.item_category.asc(), ProjectBomItem.product_id.asc())
    )
    items = db.execute(stmt).scalars().all()

    item_responses = [_build_project_bom_item_response(it) for it in items]
    total_cost = sum(it.total_planned_cost for it in item_responses)

    return APIResponse(
        success=True,
        message="Project BOM retrieved successfully",
        data=ProjectBomListResponse(
            project_id=project.id,
            project_code=project.project_code,
            system_type=project.system_type,
            system_capacity_kw=float(project.system_capacity_kw),
            items=item_responses,
            total_items=len(item_responses),
            total_estimated_cost=total_cost,
        ),
    )


@router.post("/projects/{project_id}/bom/generate", response_model=APIResponse[ProjectBomListResponse], status_code=status.HTTP_201_CREATED)
def generate_project_bom(
    project_id: int,
    payload: ProjectBomGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bom_manage_access),
):
    """
    Generate project BOM lines from an active template.
    Snapshots equipment base prices into unit_cost_snapshot.
    Enforces idempotency and prevents overwriting existing project BOMs.
    """
    project = db.execute(select(Project).where(Project.id == project_id)).scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )

    # Check if project already has BOM items
    existing_count = db.execute(
        select(func.count(ProjectBomItem.id)).where(ProjectBomItem.project_id == project_id)
    ).scalar() or 0
    if existing_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project '{project.project_code}' already contains {existing_count} BOM items. Generation rejected.",
        )

    # Validate template
    template = db.execute(
        select(BomTemplate)
        .where(BomTemplate.id == payload.template_id)
        .options(selectinload(BomTemplate.items).selectinload(BomItem.product))
    ).scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BOM template with ID {payload.template_id} not found",
        )
    if not template.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot generate project BOM from inactive template '{template.template_name}'",
        )

    # Validate compatibility
    if template.system_type.upper() != project.system_type.upper():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template system type '{template.system_type}' does not match project system type '{project.system_type}'",
        )

    if float(template.capacity_kw) != float(project.system_capacity_kw):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template capacity ({float(template.capacity_kw)} kW) does not match project capacity ({float(project.system_capacity_kw)} kW)",
        )

    if not template.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Selected template '{template.template_name}' contains no BOM component lines",
        )

    created_items = []
    try:
        for t_item in template.items:
            prod = t_item.product
            cost_snapshot = prod.base_price if prod and prod.base_price is not None else 0.00
            bom_item = ProjectBomItem(
                project_id=project.id,
                product_id=t_item.product_id,
                item_category=t_item.item_category,
                planned_quantity=t_item.default_quantity,
                allocated_quantity=0.00,
                dispatched_quantity=0.00,
                installed_quantity=0.00,
                unit_cost_snapshot=cost_snapshot,
            )
            db.add(bom_item)
            created_items.append(bom_item)

        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate component conflict during project BOM generation: {str(exc.orig) if hasattr(exc, 'orig') else str(exc)}",
        )

    _record_audit_log(
        db,
        user_id=current_user.id,
        action="BOM_GENERATE",
        entity_name="PROJECT_BOM",
        entity_id=project.id,
        details={
            "template_id": template.id,
            "template_name": template.template_name,
            "item_count": len(created_items),
        },
    )
    db.commit()

    # Reload generated lines
    stmt = (
        select(ProjectBomItem)
        .where(ProjectBomItem.project_id == project.id)
        .options(selectinload(ProjectBomItem.product))
        .order_by(ProjectBomItem.item_category.asc(), ProjectBomItem.product_id.asc())
    )
    reloaded_items = db.execute(stmt).scalars().all()
    item_responses = [_build_project_bom_item_response(it) for it in reloaded_items]
    total_cost = sum(it.total_planned_cost for it in item_responses)

    return APIResponse(
        success=True,
        message=f"Project BOM generated with {len(reloaded_items)} component lines",
        data=ProjectBomListResponse(
            project_id=project.id,
            project_code=project.project_code,
            system_type=project.system_type,
            system_capacity_kw=float(project.system_capacity_kw),
            items=item_responses,
            total_items=len(item_responses),
            total_estimated_cost=total_cost,
        ),
    )


@router.put("/projects/{project_id}/bom/items/{item_id}", response_model=APIResponse[ProjectBomItemResponse])
def update_project_bom_item_quantity(
    project_id: int,
    item_id: int,
    payload: ProjectBomItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bom_manage_access),
):
    """
    Adjust planned quantity of a project BOM item.
    Enforces invariant: planned_quantity >= allocated_quantity >= dispatched_quantity >= installed_quantity.
    Allocated, dispatched, installed, and unit_cost_snapshot remain strictly protected.
    """
    item = db.execute(
        select(ProjectBomItem)
        .where(ProjectBomItem.id == item_id, ProjectBomItem.project_id == project_id)
        .options(selectinload(ProjectBomItem.product))
    ).scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project BOM item with ID {item_id} not found in project {project_id}",
        )

    new_planned = payload.planned_quantity

    if new_planned < item.allocated_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Planned quantity ({new_planned}) cannot be less than already allocated stock ({item.allocated_quantity})",
        )

    old_planned = float(item.planned_quantity)
    item.planned_quantity = new_planned
    item.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)

    _record_audit_log(
        db,
        user_id=current_user.id,
        action="PLANNED_QTY_UPDATE",
        entity_name="PROJECT_BOM",
        entity_id=project_id,
        details={
            "item_id": item.id,
            "product_id": item.product_id,
            "old_planned": old_planned,
            "new_planned": float(new_planned),
        },
    )
    db.commit()

    return APIResponse(
        success=True,
        message="Planned quantity updated successfully",
        data=_build_project_bom_item_response(item),
    )
