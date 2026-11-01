from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_, desc
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date, timezone
from decimal import Decimal
import math

from app.database import get_db
from app.models.auth import User
from app.models.workflow import AuditLog
from app.models.crm import Product
from app.models.projects import Order, Project, ProjectBomItem
from app.models.inventory import (
    Inventory,
    StockMovement,
    StockReservation,
    SerialNumber,
    SerialNumberHistory,
    Dispatch,
    DispatchItem,
    DispatchSerial,
    DeliveryConfirmation,
)
from app.schemas.dispatch import (
    MaterialReservationCreate,
    MaterialReservationResponse,
    DispatchItemCreate,
    DispatchItemResponse,
    DispatchCreate,
    DispatchStatusUpdate,
    DeliveryConfirmationCreate,
    DeliveryConfirmationResponse,
    DispatchResponse,
    DispatchDetailResponse,
    ProjectMaterialReadinessItem,
    ProjectMaterialReadinessResponse,
    VALID_DISPATCH_STATUSES,
    VALID_CONFIRMATION_TYPES,
)
from app.schemas import APIResponse
from app.dependencies.auth import get_current_user, get_user_permissions
from app.utils.roles import SystemRole

router = APIRouter(tags=["Dispatch & Material Logistics"])


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


def require_dispatch_read_access(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role and current_user.role.slug == SystemRole.SUPER_ADMIN:
        return current_user

    if current_user.role and current_user.role.slug in {SystemRole.CUSTOMER, SystemRole.SALES}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role not authorized to access dispatch and logistics records",
        )

    user_perms = get_user_permissions(current_user)
    if (
        "dispatch.read" in user_perms
        or "dispatch.create" in user_perms
        or "inventory.read" in user_perms
        or "serials.read" in user_perms
    ):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Missing required permission: dispatch.read",
    )


def require_dispatch_manage_access(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role and current_user.role.slug == SystemRole.SUPER_ADMIN:
        return current_user

    if current_user.role and current_user.role.slug in {
        SystemRole.CUSTOMER,
        SystemRole.SALES,
        SystemRole.FIELD_TECHNICIAN,
        SystemRole.SERVICE_WARRANTY,
        SystemRole.FINANCE_ACCOUNTS,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role not authorized to manage dispatches or material reservations",
        )

    user_perms = get_user_permissions(current_user)
    if "dispatch.create" in user_perms or "inventory.manage" in user_perms:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Missing required permission: dispatch.create",
    )


def require_delivery_confirm_access(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role and current_user.role.slug == SystemRole.SUPER_ADMIN:
        return current_user

    if current_user.role and current_user.role.slug in {SystemRole.CUSTOMER, SystemRole.SALES}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role not authorized to confirm deliveries",
        )

    user_perms = get_user_permissions(current_user)
    if (
        "dispatch.confirm" in user_perms
        or "dispatch.create" in user_perms
    ):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Missing required permission: dispatch.confirm",
    )


def _generate_dispatch_number(db: Session) -> str:
    current_year = datetime.now(timezone.utc).year
    prefix = f"DISP-{current_year}-"
    latest = (
        db.execute(
            select(Dispatch.dispatch_number)
            .where(Dispatch.dispatch_number.like(f"{prefix}%"))
            .order_by(Dispatch.dispatch_number.desc())
            .with_for_update()
        )
        .scalars()
        .first()
    )
    if latest:
        try:
            seq_part = int(latest.split("-")[-1])
            seq = seq_part + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


# ==========================================
# 1. MATERIAL READINESS & RESERVATIONS
# ==========================================

@router.get("/projects/{project_id}/material-readiness", response_model=APIResponse[ProjectMaterialReadinessResponse])
@router.get("/dispatch/readiness/{project_id}", response_model=APIResponse[ProjectMaterialReadinessResponse])
@router.get("/dispatches/readiness/{project_id}", response_model=APIResponse[ProjectMaterialReadinessResponse])
def get_project_material_readiness(
    project_id: int,
    current_user: User = Depends(require_dispatch_read_access),
    db: Session = Depends(get_db),
):
    """
    Evaluate project material readiness: compares Project BOM lines with warehouse
    available stock, existing project reservations, and remaining quantities to dispatch.
    """
    project = (
        db.execute(
            select(Project)
            .options(
                selectinload(Project.order),
                selectinload(Project.customer),
                selectinload(Project.bom_items).selectinload(ProjectBomItem.product),
            )
            .where(Project.id == project_id)
        )
        .scalars()
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found",
        )

    items = []
    all_ready = True

    for bom_item in (project.bom_items or []):
        p = bom_item.product
        inv = db.execute(
            select(Inventory).where(Inventory.product_id == bom_item.product_id)
        ).scalar_one_or_none()

        qoh = inv.quantity_on_hand if inv else Decimal("0.00")
        avail = inv.quantity_available if inv else Decimal("0.00")

        # Query existing active reservations for this project and product
        proj_res_sum = db.execute(
            select(func.coalesce(func.sum(StockReservation.reserved_quantity), Decimal("0.00")))
            .where(
                StockReservation.project_id == project.id,
                StockReservation.product_id == bom_item.product_id,
                StockReservation.status == "RESERVED",
            )
        ).scalar() or Decimal("0.00")

        planned = bom_item.planned_quantity
        dispatched = bom_item.dispatched_quantity
        rem_to_dispatch = max(Decimal("0.00"), planned - dispatched)

        # Ready for dispatch if remaining is 0 OR available + already reserved for project >= remaining
        is_ready = rem_to_dispatch == Decimal("0.00") or ((avail + proj_res_sum) >= rem_to_dispatch)
        if not is_ready:
            all_ready = False

        items.append(
            ProjectMaterialReadinessItem(
                product_id=bom_item.product_id,
                product_code=p.product_code if p else "",
                product_name=p.name if p else "",
                category=p.category if p else bom_item.item_category,
                unit_of_measure=p.unit_of_measure if p else "NOS",
                is_serialized=p.is_serialized if p else False,
                planned_quantity=planned,
                allocated_quantity=bom_item.allocated_quantity,
                dispatched_quantity=dispatched,
                installed_quantity=bom_item.installed_quantity,
                remaining_to_dispatch=rem_to_dispatch,
                warehouse_on_hand=qoh,
                warehouse_available=avail,
                reserved_for_project=proj_res_sum,
                is_ready_for_dispatch=is_ready,
            )
        )

    return APIResponse(
        message=f"Material readiness for project '{project.project_code}' calculated successfully",
        data=ProjectMaterialReadinessResponse(
            project_id=project.id,
            project_code=project.project_code,
            order_id=project.order_id,
            order_number=project.order.order_number if project.order else "",
            customer_name=project.customer.full_name if project.customer else "",
            site_address=project.site_address,
            project_status=project.status,
            all_ready_for_dispatch=all_ready,
            items=items,
        ),
    )


@router.post("/dispatches/reservations", response_model=APIResponse[MaterialReservationResponse], status_code=status.HTTP_201_CREATED)
@router.post("/dispatch/reservations", response_model=APIResponse[MaterialReservationResponse], status_code=status.HTTP_201_CREATED)
def create_stock_reservation(
    payload: MaterialReservationCreate,
    current_user: User = Depends(require_dispatch_manage_access),
    db: Session = Depends(get_db),
):
    """
    Reserve available warehouse inventory for a specific solar installation project BOM.
    Atomically updates Inventory.reserved_quantity and Inventory.quantity_available.
    """
    project = db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    bom_item = db.execute(
        select(ProjectBomItem).where(
            ProjectBomItem.project_id == payload.project_id,
            ProjectBomItem.product_id == payload.product_id,
        )
    ).scalar_one_or_none()

    if not bom_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product ID {payload.product_id} is not part of the project BOM for '{project.project_code}'",
        )

    # Row-lock inventory
    inv = db.execute(
        select(Inventory).where(Inventory.product_id == payload.product_id).with_for_update()
    ).scalar_one_or_none()

    if not inv:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No warehouse inventory record exists for this product. Inward goods first.",
        )

    qty_to_res = Decimal(str(payload.reserved_quantity))
    if qty_to_res <= 0:
        raise HTTPException(status_code=400, detail="Reserved quantity must be greater than zero")

    if inv.quantity_available < qty_to_res:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient available stock. Available: {inv.quantity_available}, Requested: {qty_to_res}",
        )

    # Atomically adjust inventory
    inv.reserved_quantity += qty_to_res
    inv.quantity_available = inv.quantity_on_hand - inv.reserved_quantity

    # Update BOM allocated quantity
    bom_item.allocated_quantity += qty_to_res

    reservation = StockReservation(
        inventory_id=inv.id,
        product_id=payload.product_id,
        project_id=project.id,
        reserved_quantity=qty_to_res,
        status="RESERVED",
        reserved_by=current_user.id,
        expiry_date=payload.expiry_date,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="STOCK_RESERVATION",
        entity_name="STOCK_RESERVATION",
        entity_id=reservation.id,
        details={
            "project_code": project.project_code,
            "product_id": payload.product_id,
            "quantity": float(qty_to_res),
        },
    )
    db.commit()

    product = db.get(Product, payload.product_id)
    return APIResponse(
        message=f"Reserved {qty_to_res} units for project '{project.project_code}' successfully",
        data=MaterialReservationResponse(
            id=reservation.id,
            inventory_id=reservation.inventory_id,
            product_id=reservation.product_id,
            product_code=product.product_code if product else None,
            product_name=product.name if product else None,
            project_id=reservation.project_id,
            project_code=project.project_code,
            reserved_quantity=reservation.reserved_quantity,
            status=reservation.status,
            reserved_by=reservation.reserved_by,
            expiry_date=reservation.expiry_date,
            created_at=reservation.created_at,
        ),
    )


@router.delete("/dispatches/reservations/{reservation_id}", response_model=APIResponse[dict])
@router.delete("/dispatch/reservations/{reservation_id}", response_model=APIResponse[dict])
def release_stock_reservation(
    reservation_id: int,
    current_user: User = Depends(require_dispatch_manage_access),
    db: Session = Depends(get_db),
):
    """
    Cancel/release a material reservation and restore available warehouse inventory.
    """
    reservation = db.get(StockReservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if reservation.status != "RESERVED":
        raise HTTPException(status_code=400, detail=f"Reservation is already {reservation.status}")

    # Row-lock inventory
    inv = db.execute(
        select(Inventory).where(Inventory.product_id == reservation.product_id).with_for_update()
    ).scalar_one_or_none()
    if inv:
        inv.reserved_quantity = max(Decimal("0.00"), inv.reserved_quantity - reservation.reserved_quantity)
        inv.quantity_available = inv.quantity_on_hand - inv.reserved_quantity

    bom_item = db.execute(
        select(ProjectBomItem).where(
            ProjectBomItem.project_id == reservation.project_id,
            ProjectBomItem.product_id == reservation.product_id,
        )
    ).scalar_one_or_none()
    if bom_item:
        bom_item.allocated_quantity = max(Decimal("0.00"), bom_item.allocated_quantity - reservation.reserved_quantity)

    reservation.status = "CANCELLED"
    db.commit()

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="RELEASE_RESERVATION",
        entity_name="STOCK_RESERVATION",
        entity_id=reservation.id,
        details={"project_id": reservation.project_id, "quantity": float(reservation.reserved_quantity)},
    )
    db.commit()

    return APIResponse(message="Reservation released successfully", data={"id": reservation_id, "status": "CANCELLED"})


# ==========================================
# 2. DISPATCH ENDPOINTS
# ==========================================

@router.get("/dispatches", response_model=APIResponse[dict])
@router.get("/dispatch", response_model=APIResponse[dict])
def list_dispatches(
    project_id: Optional[int] = Query(None),
    dispatch_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_dispatch_read_access),
    db: Session = Depends(get_db),
):
    """
    List dispatches with search, filters, and pagination.
    """
    query = (
        select(Dispatch)
        .options(
            selectinload(Dispatch.project).selectinload(Project.customer),
            selectinload(Dispatch.order),
            selectinload(Dispatch.dispatcher),
            selectinload(Dispatch.items),
            selectinload(Dispatch.delivery_confirmation),
        )
    )

    if project_id:
        query = query.where(Dispatch.project_id == project_id)

    if dispatch_status:
        query = query.where(Dispatch.dispatch_status == dispatch_status.strip().upper())

    if search:
        s = f"%{search.strip()}%"
        query = query.where(
            or_(
                Dispatch.dispatch_number.ilike(s),
                Dispatch.tracking_number.ilike(s),
                Dispatch.vehicle_number.ilike(s),
                Dispatch.driver_name.ilike(s),
            )
        )

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0

    dispatches = (
        db.execute(
            query.order_by(Dispatch.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    items = []
    for d in dispatches:
        items.append(
            DispatchResponse(
                id=d.id,
                dispatch_number=d.dispatch_number,
                project_id=d.project_id,
                project_code=d.project.project_code if d.project else None,
                order_id=d.order_id,
                order_number=d.order.order_number if d.order else None,
                customer_name=d.project.customer.full_name if d.project and d.project.customer else None,
                site_address=d.project.site_address if d.project else None,
                dispatched_date=d.dispatched_date,
                dispatch_status=d.dispatch_status,
                vehicle_number=d.vehicle_number,
                driver_name=d.driver_name,
                driver_phone=d.driver_phone,
                tracking_number=d.tracking_number,
                dispatched_by=d.dispatched_by,
                dispatcher_name=d.dispatcher.full_name if d.dispatcher else None,
                remarks=d.remarks,
                items_count=len(d.items) if d.items else 0,
                is_confirmed=d.delivery_confirmation is not None,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
        )

    return APIResponse(
        message="Dispatches retrieved successfully",
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        },
    )


@router.get("/dispatches/{dispatch_id}", response_model=APIResponse[DispatchDetailResponse])
@router.get("/dispatch/{dispatch_id}", response_model=APIResponse[DispatchDetailResponse])
def get_dispatch_detail(
    dispatch_id: int,
    current_user: User = Depends(require_dispatch_read_access),
    db: Session = Depends(get_db),
):
    """
    Retrieve full dispatch note details including line items and serials.
    """
    d = (
        db.execute(
            select(Dispatch)
            .options(
                selectinload(Dispatch.project).selectinload(Project.customer),
                selectinload(Dispatch.order),
                selectinload(Dispatch.dispatcher),
                selectinload(Dispatch.items).selectinload(DispatchItem.product),
                selectinload(Dispatch.items).selectinload(DispatchItem.serials).selectinload(DispatchSerial.serial),
                selectinload(Dispatch.delivery_confirmation).selectinload(DeliveryConfirmation.confirmer),
            )
            .where(Dispatch.id == dispatch_id)
        )
        .scalars()
        .first()
    )
    if not d:
        raise HTTPException(status_code=404, detail="Dispatch not found")

    items_resp = []
    for it in (d.items or []):
        serials_resp = [
            {"serial_number_id": s.serial_number_id, "serial_number": s.serial.serial_number if s.serial else None}
            for s in (it.serials or [])
        ]
        items_resp.append(
            DispatchItemResponse(
                id=it.id,
                dispatch_id=it.dispatch_id,
                product_id=it.product_id,
                product_code=it.product.product_code if it.product else None,
                product_name=it.product.name if it.product else None,
                category=it.product.category if it.product else None,
                unit_of_measure=it.product.unit_of_measure if it.product else None,
                is_serialized=it.product.is_serialized if it.product else False,
                dispatched_quantity=it.dispatched_quantity,
                serials=serials_resp,
                created_at=it.created_at,
            )
        )

    deliv_conf = None
    if d.delivery_confirmation:
        dc = d.delivery_confirmation
        deliv_conf = DeliveryConfirmationResponse(
            id=dc.id,
            dispatch_id=dc.dispatch_id,
            project_id=dc.project_id,
            confirmed_by=dc.confirmed_by,
            confirmer_name=dc.confirmer.full_name if dc.confirmer else None,
            confirmation_type=dc.confirmation_type,
            recipient_name=dc.recipient_name,
            recipient_phone=dc.recipient_phone,
            confirmation_timestamp=dc.confirmation_timestamp,
            delivery_notes=dc.delivery_notes,
            created_at=dc.created_at,
        )

    return APIResponse(
        message="Dispatch details retrieved successfully",
        data=DispatchDetailResponse(
            id=d.id,
            dispatch_number=d.dispatch_number,
            project_id=d.project_id,
            project_code=d.project.project_code if d.project else None,
            order_id=d.order_id,
            order_number=d.order.order_number if d.order else None,
            customer_name=d.project.customer.full_name if d.project and d.project.customer else None,
            site_address=d.project.site_address if d.project else None,
            dispatched_date=d.dispatched_date,
            dispatch_status=d.dispatch_status,
            vehicle_number=d.vehicle_number,
            driver_name=d.driver_name,
            driver_phone=d.driver_phone,
            tracking_number=d.tracking_number,
            dispatched_by=d.dispatched_by,
            dispatcher_name=d.dispatcher.full_name if d.dispatcher else None,
            remarks=d.remarks,
            items_count=len(items_resp),
            is_confirmed=deliv_conf is not None,
            created_at=d.created_at,
            updated_at=d.updated_at,
            items=items_resp,
            delivery_confirmation=deliv_conf,
        ),
    )


@router.post("/dispatches", response_model=APIResponse[DispatchDetailResponse], status_code=status.HTTP_201_CREATED)
@router.post("/dispatch", response_model=APIResponse[DispatchDetailResponse], status_code=status.HTTP_201_CREATED)
def create_dispatch(
    payload: DispatchCreate,
    current_user: User = Depends(require_dispatch_manage_access),
    db: Session = Depends(get_db),
):
    """
    Create a new dispatch, deduct physical warehouse inventory, update project BOM
    dispatched quantities, and assign component serial numbers in one ACID transaction.
    """
    project = (
        db.execute(
            select(Project)
            .options(
                selectinload(Project.order),
                selectinload(Project.bom_items),
            )
            .where(Project.id == payload.project_id)
            .with_for_update()
        )
        .scalars()
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.order_id:
        raise HTTPException(status_code=400, detail="Project has no associated Order reference")

    if not payload.items:
        raise HTTPException(status_code=400, detail="Dispatch note must contain at least one line item")

    bom_items_map = {b.product_id: b for b in (project.bom_items or [])}

    # Generate sequential dispatch number
    dispatch_number = _generate_dispatch_number(db)

    dispatch = Dispatch(
        dispatch_number=dispatch_number,
        project_id=project.id,
        order_id=project.order_id,
        dispatched_date=payload.dispatched_date,
        dispatch_status="DISPATCHED",
        vehicle_number=payload.vehicle_number.strip() if payload.vehicle_number else None,
        driver_name=payload.driver_name.strip() if payload.driver_name else None,
        driver_phone=payload.driver_phone.strip() if payload.driver_phone else None,
        tracking_number=payload.tracking_number.strip() if payload.tracking_number else None,
        dispatched_by=current_user.id,
        remarks=payload.remarks.strip() if payload.remarks else None,
    )
    db.add(dispatch)
    db.flush()

    for it_in in payload.items:
        qty_to_disp = Decimal(str(it_in.dispatched_quantity))
        if qty_to_disp <= 0:
            raise HTTPException(status_code=400, detail="Dispatched quantity must be greater than zero")

        product = db.get(Product, it_in.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product ID {it_in.product_id} not found")

        if product.id not in bom_items_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.name}' is not in the project BOM",
            )
        bom_item = bom_items_map[product.id]
        bom_rem = bom_item.planned_quantity - bom_item.dispatched_quantity
        if qty_to_disp > bom_rem:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dispatched quantity {qty_to_disp} exceeds remaining BOM quantity ({bom_rem}) for '{product.name}'",
            )

        # Row-lock inventory
        inv = db.execute(
            select(Inventory).where(Inventory.product_id == product.id).with_for_update()
        ).scalar_one_or_none()

        if not inv or inv.quantity_on_hand < qty_to_disp:
            avail_qoh = inv.quantity_on_hand if inv else Decimal("0.00")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient physical stock for '{product.name}'. On hand: {avail_qoh}, Requested dispatch: {qty_to_disp}",
            )

        # Check existing active project reservations
        active_res = db.execute(
            select(StockReservation)
            .where(
                StockReservation.project_id == project.id,
                StockReservation.product_id == product.id,
                StockReservation.status == "RESERVED",
            )
            .with_for_update()
        ).scalars().all()

        qty_from_reservation = Decimal("0.00")
        for res_row in active_res:
            res_remaining = res_row.reserved_quantity
            if res_remaining <= (qty_to_disp - qty_from_reservation):
                qty_from_reservation += res_remaining
                res_row.status = "FULFILLED"
            else:
                rem_needed = qty_to_disp - qty_from_reservation
                res_row.reserved_quantity -= rem_needed
                qty_from_reservation += rem_needed
                break

        # Adjust inventory quantities
        old_qoh = inv.quantity_on_hand
        inv.quantity_on_hand -= qty_to_disp
        if qty_from_reservation > Decimal("0.00"):
            inv.reserved_quantity = max(Decimal("0.00"), inv.reserved_quantity - qty_from_reservation)
        inv.quantity_available = max(Decimal("0.00"), inv.quantity_on_hand - inv.reserved_quantity)
        new_qoh = inv.quantity_on_hand

        # Create DispatchItem
        disp_item = DispatchItem(
            dispatch_id=dispatch.id,
            product_id=product.id,
            dispatched_quantity=qty_to_disp,
        )
        db.add(disp_item)
        db.flush()

        # Update Project BOM dispatched quantity
        if product.id in bom_items_map:
            bom_item = bom_items_map[product.id]
            bom_item.dispatched_quantity += qty_to_disp

        # Record StockMovement (Negative quantity for outward dispatch)
        movement = StockMovement(
            inventory_id=inv.id,
            product_id=product.id,
            movement_type="DISPATCH",
            reference_type="DISPATCH",
            reference_id=dispatch.id,
            quantity=-qty_to_disp,
            unit_cost=inv.average_unit_cost,
            quantity_before=old_qoh,
            quantity_after=new_qoh,
            performed_by=current_user.id,
            remarks=f"Dispatch {dispatch.dispatch_number} to site for project {project.project_code}",
        )
        db.add(movement)

        # Serial Number scanning for serialized products
        if product.is_serialized:
            expected_serials_count = int(qty_to_disp)
            serial_ids = it_in.serial_number_ids or []
            if len(serial_ids) != expected_serials_count:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Serialized component '{product.name}' requires exactly {expected_serials_count} scanned serial numbers, but {len(serial_ids)} were provided",
                )

            # Row-lock serials
            serials_db = db.execute(
                select(SerialNumber)
                .where(SerialNumber.id.in_(serial_ids))
                .with_for_update()
            ).scalars().all()

            if len(serials_db) != len(serial_ids):
                raise HTTPException(status_code=400, detail="One or more specified serial IDs do not exist")

            for sn in serials_db:
                if sn.product_id != product.id:
                    raise HTTPException(status_code=400, detail=f"Serial '{sn.serial_number}' does not match product '{product.name}'")
                if sn.status != "IN_STOCK":
                    raise HTTPException(status_code=400, detail=f"Serial '{sn.serial_number}' is not IN_STOCK (Current: '{sn.status}')")

                # Transition serial status to DISPATCHED
                sn.status = "DISPATCHED"
                sn.project_id = project.id

                # Link to dispatch
                disp_serial = DispatchSerial(
                    dispatch_item_id=disp_item.id,
                    serial_number_id=sn.id,
                    scanned_by=current_user.id,
                )
                db.add(disp_serial)

                # Record history
                history = SerialNumberHistory(
                    serial_number_id=sn.id,
                    previous_status="IN_STOCK",
                    new_status="DISPATCHED",
                    project_id=project.id,
                    action_taken="DISPATCHED_TO_SITE",
                    recorded_by=current_user.id,
                    remarks=f"Dispatched via note {dispatch.dispatch_number}",
                )
                db.add(history)

    # Transition Project status to DISPATCHED if materials have moved
    if project.status in {"COMMITTED", "PROCUREMENT", "INITIATED"}:
        project.status = "DISPATCHED"

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Database integrity conflict during dispatch: {str(e.orig)}",
        )

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="DISPATCH_CREATE",
        entity_name="DISPATCH",
        entity_id=dispatch.id,
        details={
            "dispatch_number": dispatch.dispatch_number,
            "project_code": project.project_code,
            "items_count": len(payload.items),
        },
    )
    db.commit()

    return APIResponse(
        message=f"Dispatch '{dispatch.dispatch_number}' created and materials deducted from warehouse successfully",
        data=_build_dispatch_detail(db, dispatch.id),
    )


@router.patch("/dispatches/{dispatch_id}/status", response_model=APIResponse[DispatchResponse])
@router.patch("/dispatch/{dispatch_id}/status", response_model=APIResponse[DispatchResponse])
def update_dispatch_status(
    dispatch_id: int,
    payload: DispatchStatusUpdate,
    current_user: User = Depends(require_dispatch_manage_access),
    db: Session = Depends(get_db),
):
    """
    Update dispatch shipment tracking status (PREPARED, DISPATCHED, IN_TRANSIT, DELIVERED, RETURNED).
    """
    dispatch = db.get(Dispatch, dispatch_id)
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")

    target = payload.dispatch_status.strip().upper()
    if target not in VALID_DISPATCH_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{target}'. Must be one of: {', '.join(VALID_DISPATCH_STATUSES)}",
        )

    dispatch.dispatch_status = target
    if payload.remarks:
        dispatch.remarks = f"{dispatch.remarks or ''}\nStatus update: {payload.remarks}".strip()

    db.commit()

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="DISPATCH_STATUS_UPDATE",
        entity_name="DISPATCH",
        entity_id=dispatch.id,
        details={"new_status": target},
    )
    db.commit()

    return APIResponse(
        message=f"Dispatch status updated to '{target}' successfully",
        data=_build_dispatch_summary(db, dispatch.id),
    )


@router.post("/dispatches/{dispatch_id}/delivery-confirm", response_model=APIResponse[DispatchResponse])
@router.post("/dispatches/{dispatch_id}/confirm", response_model=APIResponse[DispatchResponse])
@router.post("/dispatch/{dispatch_id}/delivery-confirm", response_model=APIResponse[DispatchResponse])
@router.post("/dispatch/{dispatch_id}/confirm", response_model=APIResponse[DispatchResponse])
def confirm_delivery(
    dispatch_id: int,
    payload: DeliveryConfirmationCreate,
    current_user: User = Depends(require_delivery_confirm_access),
    db: Session = Depends(get_db),
):
    """
    Confirm on-site delivery of dispatched materials.
    Updates dispatch.dispatch_status to 'DELIVERED'. Does NOT deduct inventory a second time.
    """
    dispatch = db.get(Dispatch, dispatch_id)
    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")

    existing_conf = db.execute(
        select(DeliveryConfirmation).where(DeliveryConfirmation.dispatch_id == dispatch_id)
    ).scalar_one_or_none()

    if existing_conf:
        raise HTTPException(status_code=400, detail="Delivery has already been confirmed for this dispatch")

    confirmation = DeliveryConfirmation(
        dispatch_id=dispatch.id,
        project_id=dispatch.project_id,
        confirmed_by=current_user.id,
        confirmation_type=payload.confirmation_type,
        recipient_name=payload.recipient_name.strip(),
        recipient_phone=payload.recipient_phone.strip(),
        delivery_notes=payload.delivery_notes.strip() if payload.delivery_notes else None,
    )
    db.add(confirmation)

    dispatch.dispatch_status = "DELIVERED"
    db.commit()
    db.refresh(confirmation)

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="DELIVERY_CONFIRM",
        entity_name="DELIVERY_CONFIRMATION",
        entity_id=confirmation.id,
        details={
            "dispatch_number": dispatch.dispatch_number,
            "recipient_name": confirmation.recipient_name,
        },
    )
    db.commit()

    return APIResponse(
        message=f"Delivery confirmation recorded for dispatch '{dispatch.dispatch_number}' successfully",
        data=_build_dispatch_summary(db, dispatch.id),
    )


def _build_dispatch_summary(db: Session, dispatch_id: int) -> DispatchResponse:
    d = (
        db.execute(
            select(Dispatch)
            .options(
                selectinload(Dispatch.project).selectinload(Project.customer),
                selectinload(Dispatch.order),
                selectinload(Dispatch.dispatcher),
                selectinload(Dispatch.items),
                selectinload(Dispatch.delivery_confirmation),
            )
            .where(Dispatch.id == dispatch_id)
        )
        .scalars()
        .first()
    )
    return DispatchResponse(
        id=d.id,
        dispatch_number=d.dispatch_number,
        project_id=d.project_id,
        project_code=d.project.project_code if d.project else None,
        order_id=d.order_id,
        order_number=d.order.order_number if d.order else None,
        customer_name=d.project.customer.full_name if d.project and d.project.customer else None,
        site_address=d.project.site_address if d.project else None,
        dispatched_date=d.dispatched_date,
        dispatch_status=d.dispatch_status,
        vehicle_number=d.vehicle_number,
        driver_name=d.driver_name,
        driver_phone=d.driver_phone,
        tracking_number=d.tracking_number,
        dispatched_by=d.dispatched_by,
        dispatcher_name=d.dispatcher.full_name if d.dispatcher else None,
        remarks=d.remarks,
        items_count=len(d.items) if d.items else 0,
        is_confirmed=d.delivery_confirmation is not None,
        created_at=d.created_at,
        updated_at=d.updated_at,
    )


def _build_dispatch_detail(db: Session, dispatch_id: int) -> DispatchDetailResponse:
    d = (
        db.execute(
            select(Dispatch)
            .options(
                selectinload(Dispatch.project).selectinload(Project.customer),
                selectinload(Dispatch.order),
                selectinload(Dispatch.dispatcher),
                selectinload(Dispatch.items).selectinload(DispatchItem.product),
                selectinload(Dispatch.items).selectinload(DispatchItem.serials).selectinload(DispatchSerial.serial),
                selectinload(Dispatch.delivery_confirmation).selectinload(DeliveryConfirmation.confirmer),
            )
            .where(Dispatch.id == dispatch_id)
        )
        .scalars()
        .first()
    )

    items_resp = []
    for it in (d.items or []):
        serials_resp = [
            {"serial_number_id": s.serial_number_id, "serial_number": s.serial.serial_number if s.serial else None}
            for s in (it.serials or [])
        ]
        items_resp.append(
            DispatchItemResponse(
                id=it.id,
                dispatch_id=it.dispatch_id,
                product_id=it.product_id,
                product_code=it.product.product_code if it.product else None,
                product_name=it.product.name if it.product else None,
                category=it.product.category if it.product else None,
                unit_of_measure=it.product.unit_of_measure if it.product else None,
                is_serialized=it.product.is_serialized if it.product else False,
                dispatched_quantity=it.dispatched_quantity,
                serials=serials_resp,
                created_at=it.created_at,
            )
        )

    deliv_conf = None
    if d.delivery_confirmation:
        dc = d.delivery_confirmation
        deliv_conf = DeliveryConfirmationResponse(
            id=dc.id,
            dispatch_id=dc.dispatch_id,
            project_id=dc.project_id,
            confirmed_by=dc.confirmed_by,
            confirmer_name=dc.confirmer.full_name if dc.confirmer else None,
            confirmation_type=dc.confirmation_type,
            recipient_name=dc.recipient_name,
            recipient_phone=dc.recipient_phone,
            confirmation_timestamp=dc.confirmation_timestamp,
            delivery_notes=dc.delivery_notes,
            created_at=dc.created_at,
        )

    return DispatchDetailResponse(
        id=d.id,
        dispatch_number=d.dispatch_number,
        project_id=d.project_id,
        project_code=d.project.project_code if d.project else None,
        order_id=d.order_id,
        order_number=d.order.order_number if d.order else None,
        customer_name=d.project.customer.full_name if d.project and d.project.customer else None,
        site_address=d.project.site_address if d.project else None,
        dispatched_date=d.dispatched_date,
        dispatch_status=d.dispatch_status,
        vehicle_number=d.vehicle_number,
        driver_name=d.driver_name,
        driver_phone=d.driver_phone,
        tracking_number=d.tracking_number,
        dispatched_by=d.dispatched_by,
        dispatcher_name=d.dispatcher.full_name if d.dispatcher else None,
        remarks=d.remarks,
        items_count=len(items_resp),
        is_confirmed=deliv_conf is not None,
        created_at=d.created_at,
        updated_at=d.updated_at,
        items=items_resp,
        delivery_confirmation=deliv_conf,
    )
