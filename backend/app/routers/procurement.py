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
from app.models.projects import (
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
    GoodsReceipt,
    GoodsReceiptItem,
    Project,
    ProjectBomItem,
)
from app.models.inventory import Inventory, StockMovement, SerialNumber
from app.schemas.procurement import (
    SupplierCreate,
    SupplierUpdate,
    SupplierStatusUpdate,
    SupplierResponse,
    SupplierListResponse,
    PurchaseOrderItemCreate,
    PurchaseOrderItemResponse,
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderResponse,
    PurchaseOrderDetailResponse,
    GoodsReceiptItemCreate,
    GoodsReceiptItemResponse,
    GoodsReceiptCreate,
    GoodsReceiptResponse,
    GoodsReceiptDetailResponse,
    InventoryItemResponse,
    StockMovementResponse,
    SerialNumberResponse,
    ProjectMaterialShortageItem,
    ProjectMaterialShortageResponse,
    VALID_PO_STATUSES,
    VALID_GRN_STATUSES,
)
from app.schemas import APIResponse
from app.dependencies.auth import get_current_user, get_user_permissions
from app.utils.roles import SystemRole

router = APIRouter(prefix="", tags=["Procurement & Inventory"])


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


def require_procurement_read_access(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure user has read permission for procurement and purchase orders.
    SUPER_ADMIN has universal access.
    CUSTOMER and SALES are strictly forbidden.
    Other roles require 'procurement.read', 'procurement.manage', or 'suppliers.manage'.
    """
    if current_user.role and current_user.role.slug == SystemRole.SUPER_ADMIN:
        return current_user

    if current_user.role and current_user.role.slug in {SystemRole.CUSTOMER, SystemRole.SALES}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role not authorized to access procurement data",
        )

    user_perms = get_user_permissions(current_user)
    if (
        "procurement.read" in user_perms
        or "procurement.manage" in user_perms
        or "suppliers.manage" in user_perms
    ):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Missing required permission: procurement.read",
    )


def require_procurement_manage_access(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure user has write permission for procurement and purchase orders.
    Held by SUPER_ADMIN, WAREHOUSE_PROCUREMENT.
    """
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
            detail="Role not authorized to modify procurement or inventory records",
        )

    user_perms = get_user_permissions(current_user)
    if "procurement.manage" in user_perms:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Missing required permission: procurement.manage",
    )


def require_supplier_manage_access(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure user has write permission for suppliers.
    Held by SUPER_ADMIN, WAREHOUSE_PROCUREMENT.
    """
    if current_user.role and current_user.role.slug == SystemRole.SUPER_ADMIN:
        return current_user

    if current_user.role and current_user.role.slug in {SystemRole.CUSTOMER, SystemRole.SALES}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role not authorized to manage suppliers",
        )

    user_perms = get_user_permissions(current_user)
    if "suppliers.manage" in user_perms:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Missing required permission: suppliers.manage",
    )


def require_inventory_read_access(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure user has read permission for inventory balances.
    Held by SUPER_ADMIN, DIRECTOR, TECHNICAL_MANAGER, WAREHOUSE_PROCUREMENT.
    """
    if current_user.role and current_user.role.slug == SystemRole.SUPER_ADMIN:
        return current_user

    if current_user.role and current_user.role.slug in {SystemRole.CUSTOMER, SystemRole.SALES}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role not authorized to access inventory records",
        )

    user_perms = get_user_permissions(current_user)
    if "inventory.read" in user_perms or "inventory.manage" in user_perms:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Missing required permission: inventory.read",
    )


def require_serials_read_access(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure user has read permission for component serial numbers.
    Held by SUPER_ADMIN, DIRECTOR, TECHNICAL_MANAGER, WAREHOUSE_PROCUREMENT, FIELD_TECHNICIAN, SERVICE_WARRANTY.
    """
    if current_user.role and current_user.role.slug == SystemRole.SUPER_ADMIN:
        return current_user

    if current_user.role and current_user.role.slug in {SystemRole.CUSTOMER, SystemRole.SALES}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role not authorized to access serial numbers",
        )

    user_perms = get_user_permissions(current_user)
    if "serials.read" in user_perms or "inventory.read" in user_perms or "serials.manage" in user_perms:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Missing required permission: serials.read",
    )


def _generate_po_number(db: Session) -> str:
    current_year = datetime.now(timezone.utc).year
    prefix = f"PO-{current_year}-"
    # Find max existing po_number with this prefix
    latest_po = (
        db.execute(
            select(PurchaseOrder.po_number)
            .where(PurchaseOrder.po_number.like(f"{prefix}%"))
            .order_by(PurchaseOrder.po_number.desc())
            .with_for_update()
        )
        .scalars()
        .first()
    )
    if latest_po:
        try:
            seq_part = int(latest_po.split("-")[-1])
            seq = seq_part + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


def _generate_grn_number(db: Session) -> str:
    current_year = datetime.now(timezone.utc).year
    prefix = f"GRN-{current_year}-"
    latest_grn = (
        db.execute(
            select(GoodsReceipt.grn_number)
            .where(GoodsReceipt.grn_number.like(f"{prefix}%"))
            .order_by(GoodsReceipt.grn_number.desc())
            .with_for_update()
        )
        .scalars()
        .first()
    )
    if latest_grn:
        try:
            seq_part = int(latest_grn.split("-")[-1])
            seq = seq_part + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


def _generate_supplier_code(db: Session) -> str:
    max_id = db.execute(select(func.coalesce(func.max(Supplier.id), 0))).scalar() or 0
    return f"SUP-{max_id + 1:04d}"


# ==========================================
# 1. SUPPLIER ENDPOINTS
# ==========================================

@router.get("/suppliers", response_model=APIResponse[dict])
def list_suppliers(
    search: Optional[str] = Query(None, description="Search by name, code, contact, city, state"),
    is_active: Optional[bool] = Query(None, description="Filter active/inactive"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_procurement_read_access),
    db: Session = Depends(get_db),
):
    """
    List suppliers with search, filtering, and pagination.
    """
    query = select(Supplier)

    if search:
        s = f"%{search.strip()}%"
        query = query.where(
            or_(
                Supplier.company_name.ilike(s),
                Supplier.supplier_code.ilike(s),
                Supplier.contact_person.ilike(s),
                Supplier.city.ilike(s),
                Supplier.state.ilike(s),
            )
        )

    if is_active is not None:
        query = query.where(Supplier.is_active == is_active)

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0

    suppliers = (
        db.execute(
            query.order_by(Supplier.company_name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    items = [SupplierListResponse.model_validate(s) for s in suppliers]

    return APIResponse(
        message="Suppliers retrieved successfully",
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        },
    )


@router.post("/suppliers", response_model=APIResponse[SupplierResponse], status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreate,
    current_user: User = Depends(require_supplier_manage_access),
    db: Session = Depends(get_db),
):
    """
    Register a new equipment/component supplier.
    Enforces uniqueness of company name, supplier code, and GST number.
    """
    company_name_clean = payload.company_name.strip()

    # Uniqueness check: company_name
    existing_name = db.execute(
        select(Supplier).where(func.lower(Supplier.company_name) == company_name_clean.lower())
    ).scalar_one_or_none()
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Supplier with company name '{company_name_clean}' already exists",
        )

    # Determine supplier code
    code = (payload.supplier_code or "").strip().upper()
    if not code:
        code = _generate_supplier_code(db)
    else:
        existing_code = db.execute(
            select(Supplier).where(func.lower(Supplier.supplier_code) == code.lower())
        ).scalar_one_or_none()
        if existing_code:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Supplier with code '{code}' already exists",
            )

    # Uniqueness check: GST if provided
    gst = payload.gst_number.strip().upper() if payload.gst_number and payload.gst_number.strip() else None
    if gst:
        existing_gst = db.execute(
            select(Supplier).where(func.lower(Supplier.gst_number) == gst.lower())
        ).scalar_one_or_none()
        if existing_gst:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Supplier with GST number '{gst}' already registered",
            )

    supplier = Supplier(
        supplier_code=code,
        company_name=company_name_clean,
        contact_person=payload.contact_person.strip(),
        email=payload.email.strip().lower(),
        phone=payload.phone.strip(),
        address=payload.address.strip(),
        city=payload.city.strip(),
        state=payload.state.strip(),
        gst_number=gst,
        pan_number=payload.pan_number.strip().upper() if payload.pan_number and payload.pan_number.strip() else None,
        bank_account_details=payload.bank_account_details.strip() if payload.bank_account_details else None,
        is_active=True,
    )

    db.add(supplier)
    try:
        db.commit()
        db.refresh(supplier)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Database constraint error creating supplier: {str(e.orig)}",
        )

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="SUPPLIER_CREATE",
        entity_name="SUPPLIER",
        entity_id=supplier.id,
        details={"supplier_code": supplier.supplier_code, "company_name": supplier.company_name},
    )
    db.commit()

    return APIResponse(
        message=f"Supplier '{supplier.company_name}' registered successfully",
        data=SupplierResponse.model_validate(supplier),
    )


@router.get("/suppliers/{supplier_id}", response_model=APIResponse[SupplierResponse])
def get_supplier_detail(
    supplier_id: int,
    current_user: User = Depends(require_procurement_read_access),
    db: Session = Depends(get_db),
):
    """
    Retrieve full supplier profile including bank details.
    """
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found",
        )

    return APIResponse(
        message="Supplier details retrieved successfully",
        data=SupplierResponse.model_validate(supplier),
    )


@router.put("/suppliers/{supplier_id}", response_model=APIResponse[SupplierResponse])
def update_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    current_user: User = Depends(require_supplier_manage_access),
    db: Session = Depends(get_db),
):
    """
    Update supplier information. Preserves historical relationships.
    """
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found",
        )

    if payload.company_name is not None:
        name_clean = payload.company_name.strip()
        existing_name = db.execute(
            select(Supplier).where(
                func.lower(Supplier.company_name) == name_clean.lower(),
                Supplier.id != supplier_id,
            )
        ).scalar_one_or_none()
        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Supplier with company name '{name_clean}' already exists",
            )
        supplier.company_name = name_clean

    if payload.gst_number is not None:
        gst_clean = payload.gst_number.strip().upper() if payload.gst_number.strip() else None
        if gst_clean:
            existing_gst = db.execute(
                select(Supplier).where(
                    func.lower(Supplier.gst_number) == gst_clean.lower(),
                    Supplier.id != supplier_id,
                )
            ).scalar_one_or_none()
            if existing_gst:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"GST number '{gst_clean}' is already registered to another supplier",
                )
        supplier.gst_number = gst_clean

    if payload.contact_person is not None:
        supplier.contact_person = payload.contact_person.strip()
    if payload.email is not None:
        supplier.email = payload.email.strip().lower()
    if payload.phone is not None:
        supplier.phone = payload.phone.strip()
    if payload.address is not None:
        supplier.address = payload.address.strip()
    if payload.city is not None:
        supplier.city = payload.city.strip()
    if payload.state is not None:
        supplier.state = payload.state.strip()
    if payload.pan_number is not None:
        supplier.pan_number = payload.pan_number.strip().upper() if payload.pan_number.strip() else None
    if payload.bank_account_details is not None:
        supplier.bank_account_details = payload.bank_account_details.strip() if payload.bank_account_details else None
    if payload.is_active is not None:
        supplier.is_active = payload.is_active

    try:
        db.commit()
        db.refresh(supplier)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Database conflict updating supplier: {str(e.orig)}",
        )

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="SUPPLIER_UPDATE",
        entity_name="SUPPLIER",
        entity_id=supplier.id,
        details={"company_name": supplier.company_name},
    )
    db.commit()

    return APIResponse(
        message=f"Supplier '{supplier.company_name}' updated successfully",
        data=SupplierResponse.model_validate(supplier),
    )


@router.patch("/suppliers/{supplier_id}/status", response_model=APIResponse[SupplierResponse])
def update_supplier_status(
    supplier_id: int,
    payload: SupplierStatusUpdate,
    current_user: User = Depends(require_supplier_manage_access),
    db: Session = Depends(get_db),
):
    """
    Activate or deactivate supplier. Historical transactions remain preserved.
    """
    supplier = db.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found",
        )

    supplier.is_active = payload.is_active
    db.commit()
    db.refresh(supplier)

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="SUPPLIER_STATUS_UPDATE",
        entity_name="SUPPLIER",
        entity_id=supplier.id,
        details={"is_active": supplier.is_active},
    )
    db.commit()

    status_str = "activated" if supplier.is_active else "deactivated"
    return APIResponse(
        message=f"Supplier '{supplier.company_name}' {status_str} successfully",
        data=SupplierResponse.model_validate(supplier),
    )


# ==========================================
# 2. PURCHASE ORDER ENDPOINTS
# ==========================================

@router.get("/purchase-orders", response_model=APIResponse[dict])
def list_purchase_orders(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (DRAFT, ISSUED, PARTIALLY_RECEIVED, RECEIVED, CANCELLED)"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    search: Optional[str] = Query(None, description="Search by PO number or supplier name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_procurement_read_access),
    db: Session = Depends(get_db),
):
    """
    List purchase orders with status filtering, search, and pagination.
    """
    query = (
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.supplier),
            selectinload(PurchaseOrder.project),
            selectinload(PurchaseOrder.creator),
            selectinload(PurchaseOrder.items),
        )
    )

    if status_filter:
        sf = status_filter.strip().upper()
        if sf in VALID_PO_STATUSES:
            query = query.where(PurchaseOrder.status == sf)

    if supplier_id:
        query = query.where(PurchaseOrder.supplier_id == supplier_id)

    if project_id:
        query = query.where(PurchaseOrder.project_id == project_id)

    if search:
        s = f"%{search.strip()}%"
        query = query.join(Supplier, PurchaseOrder.supplier_id == Supplier.id).where(
            or_(
                PurchaseOrder.po_number.ilike(s),
                Supplier.company_name.ilike(s),
                Supplier.supplier_code.ilike(s),
            )
        )

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0

    orders = (
        db.execute(
            query.order_by(PurchaseOrder.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    items = []
    for po in orders:
        items.append(
            PurchaseOrderResponse(
                id=po.id,
                po_number=po.po_number,
                supplier_id=po.supplier_id,
                supplier_name=po.supplier.company_name if po.supplier else None,
                supplier_code=po.supplier.supplier_code if po.supplier else None,
                project_id=po.project_id,
                project_code=po.project.project_code if po.project else None,
                po_date=po.po_date,
                expected_delivery_date=po.expected_delivery_date,
                total_amount=po.total_amount,
                tax_amount=po.tax_amount,
                status=po.status,
                created_by=po.created_by,
                creator_name=po.creator.full_name if po.creator else None,
                notes=po.notes,
                items_count=len(po.items) if po.items else 0,
                created_at=po.created_at,
                updated_at=po.updated_at,
            )
        )

    return APIResponse(
        message="Purchase orders retrieved successfully",
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        },
    )


@router.post("/purchase-orders", response_model=APIResponse[PurchaseOrderDetailResponse], status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    payload: PurchaseOrderCreate,
    current_user: User = Depends(require_procurement_manage_access),
    db: Session = Depends(get_db),
):
    """
    Create a new Purchase Order in DRAFT status with atomic line items calculation.
    """
    # 1. Validate Supplier
    supplier = db.get(Supplier, payload.supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {payload.supplier_id} not found",
        )
    if not supplier.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create PO for inactive supplier '{supplier.company_name}'",
        )

    # 2. Validate Project if linked
    project = None
    if payload.project_id:
        project = db.get(Project, payload.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {payload.project_id} not found",
            )

    # 3. Validate Date ordering
    if payload.expected_delivery_date and payload.expected_delivery_date < payload.po_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="expected_delivery_date cannot be earlier than po_date",
        )

    # 4. Validate Items and calculate line values
    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase order must have at least one line item",
        )

    po_items_to_create = []
    total_tax = Decimal("0.00")
    grand_total = Decimal("0.00")

    for item_in in payload.items:
        product = db.get(Product, item_in.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {item_in.product_id} not found",
            )
        if not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.name}' is inactive and cannot be ordered",
            )

        qty = Decimal(str(item_in.ordered_quantity))
        price = Decimal(str(item_in.unit_price))
        if qty <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ordered quantity must be greater than zero")
        if price < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unit price cannot be negative")

        tax_rate = Decimal(str(item_in.tax_rate_percent if item_in.tax_rate_percent is not None else product.tax_rate_percent or "12.00"))
        
        # Financial arithmetic: subtotal, tax, total
        subtotal = round(qty * price, 2)
        tax = round(subtotal * (tax_rate / Decimal("100")), 2)
        line_total = subtotal + tax

        total_tax += tax
        grand_total += line_total

        po_item = PurchaseOrderItem(
            product_id=product.id,
            ordered_quantity=qty,
            received_quantity=Decimal("0.00"),
            unit_price=price,
            tax_rate_percent=tax_rate,
            total_amount=line_total,
        )
        po_items_to_create.append(po_item)

    # 5. Generate PO Number
    po_number = _generate_po_number(db)

    # 6. Create PurchaseOrder instance
    po = PurchaseOrder(
        po_number=po_number,
        supplier_id=supplier.id,
        project_id=project.id if project else None,
        po_date=payload.po_date,
        expected_delivery_date=payload.expected_delivery_date,
        total_amount=grand_total,
        tax_amount=total_tax,
        status="DRAFT",
        created_by=current_user.id,
        notes=payload.notes.strip() if payload.notes else None,
        items=po_items_to_create,
    )

    db.add(po)
    try:
        db.commit()
        db.refresh(po)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Database conflict creating purchase order: {str(e.orig)}",
        )

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="PO_CREATE",
        entity_name="PURCHASE_ORDER",
        entity_id=po.id,
        details={"po_number": po.po_number, "supplier_id": po.supplier_id, "total_amount": float(po.total_amount)},
    )
    db.commit()

    return APIResponse(
        message=f"Purchase order '{po.po_number}' created successfully in DRAFT",
        data=_build_po_detail_response(db, po.id),
    )


@router.get("/purchase-orders/{po_id}", response_model=APIResponse[PurchaseOrderDetailResponse])
def get_purchase_order_detail(
    po_id: int,
    current_user: User = Depends(require_procurement_read_access),
    db: Session = Depends(get_db),
):
    """
    Retrieve full details of a purchase order with items and product information.
    """
    po_resp = _build_po_detail_response(db, po_id)
    return APIResponse(
        message="Purchase order details retrieved successfully",
        data=po_resp,
    )


@router.put("/purchase-orders/{po_id}", response_model=APIResponse[PurchaseOrderDetailResponse])
def update_purchase_order(
    po_id: int,
    payload: PurchaseOrderUpdate,
    current_user: User = Depends(require_procurement_manage_access),
    db: Session = Depends(get_db),
):
    """
    Update a DRAFT purchase order. Issued or received POs cannot be edited.
    """
    po = db.get(PurchaseOrder, po_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID {po_id} not found",
        )

    if po.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only DRAFT purchase orders may be edited. This PO is currently '{po.status}'",
        )

    if payload.supplier_id is not None:
        supp = db.get(Supplier, payload.supplier_id)
        if not supp or not supp.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected supplier is invalid or inactive")
        po.supplier_id = supp.id

    if payload.project_id is not None:
        if payload.project_id == 0:
            po.project_id = None
        else:
            proj = db.get(Project, payload.project_id)
            if not proj:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
            po.project_id = proj.id

    if payload.expected_delivery_date is not None:
        if payload.expected_delivery_date < po.po_date:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="expected_delivery_date cannot be earlier than po_date")
        po.expected_delivery_date = payload.expected_delivery_date

    if payload.notes is not None:
        po.notes = payload.notes.strip() if payload.notes else None

    # Replace items if provided
    if payload.items is not None:
        if not payload.items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PO must have at least one line item")

        # Clear existing items
        po.items.clear()
        total_tax = Decimal("0.00")
        grand_total = Decimal("0.00")

        for it_in in payload.items:
            product = db.get(Product, it_in.product_id)
            if not product or not product.is_active:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid or inactive product ID {it_in.product_id}")

            qty = Decimal(str(it_in.ordered_quantity))
            price = Decimal(str(it_in.unit_price))
            tax_rate = Decimal(str(it_in.tax_rate_percent if it_in.tax_rate_percent is not None else product.tax_rate_percent or "12.00"))

            subtotal = round(qty * price, 2)
            tax = round(subtotal * (tax_rate / Decimal("100")), 2)
            line_total = subtotal + tax

            total_tax += tax
            grand_total += line_total

            new_item = PurchaseOrderItem(
                product_id=product.id,
                ordered_quantity=qty,
                received_quantity=Decimal("0.00"),
                unit_price=price,
                tax_rate_percent=tax_rate,
                total_amount=line_total,
            )
            po.items.append(new_item)

        po.total_amount = grand_total
        po.tax_amount = total_tax

    db.commit()

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="PO_UPDATE",
        entity_name="PURCHASE_ORDER",
        entity_id=po.id,
        details={"po_number": po.po_number, "total_amount": float(po.total_amount)},
    )
    db.commit()

    return APIResponse(
        message=f"Purchase order '{po.po_number}' updated successfully",
        data=_build_po_detail_response(db, po.id),
    )


@router.post("/purchase-orders/{po_id}/issue", response_model=APIResponse[PurchaseOrderDetailResponse])
def issue_purchase_order(
    po_id: int,
    current_user: User = Depends(require_procurement_manage_access),
    db: Session = Depends(get_db),
):
    """
    Transition a purchase order from DRAFT to ISSUED.
    Operational policy: WAREHOUSE_PROCUREMENT and SUPER_ADMIN may issue POs.
    """
    po = db.get(PurchaseOrder, po_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID {po_id} not found",
        )

    if po.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot issue purchase order in status '{po.status}'. Only DRAFT orders can be issued",
        )

    po.status = "ISSUED"
    db.commit()

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="PO_ISSUE",
        entity_name="PURCHASE_ORDER",
        entity_id=po.id,
        details={"po_number": po.po_number, "status": "ISSUED"},
    )
    db.commit()

    return APIResponse(
        message=f"Purchase order '{po.po_number}' issued successfully to supplier",
        data=_build_po_detail_response(db, po.id),
    )


@router.post("/purchase-orders/{po_id}/cancel", response_model=APIResponse[PurchaseOrderDetailResponse])
def cancel_purchase_order(
    po_id: int,
    current_user: User = Depends(require_procurement_manage_access),
    db: Session = Depends(get_db),
):
    """
    Cancel a purchase order.
    Allowed only if no goods receipts exist and status is not already CANCELLED, RECEIVED, or PARTIALLY_RECEIVED.
    """
    po = db.get(PurchaseOrder, po_id)
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID {po_id} not found",
        )

    if po.status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase order is already cancelled",
        )

    if po.status in {"RECEIVED", "PARTIALLY_RECEIVED"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel purchase order '{po.po_number}' with received goods. Current status: '{po.status}'",
        )

    # Verify no GRNs exist
    grn_count = db.execute(
        select(func.count(GoodsReceipt.id)).where(GoodsReceipt.purchase_order_id == po.id)
    ).scalar() or 0
    if grn_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel purchase order '{po.po_number}' with existing Goods Receipt records",
        )

    po.status = "CANCELLED"
    db.commit()

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="PO_CANCEL",
        entity_name="PURCHASE_ORDER",
        entity_id=po.id,
        details={"po_number": po.po_number, "status": "CANCELLED"},
    )
    db.commit()

    return APIResponse(
        message=f"Purchase order '{po.po_number}' cancelled successfully",
        data=_build_po_detail_response(db, po.id),
    )


def _build_po_detail_response(db: Session, po_id: int) -> PurchaseOrderDetailResponse:
    po = (
        db.execute(
            select(PurchaseOrder)
            .options(
                selectinload(PurchaseOrder.supplier),
                selectinload(PurchaseOrder.project),
                selectinload(PurchaseOrder.creator),
                selectinload(PurchaseOrder.items).selectinload(PurchaseOrderItem.product),
            )
            .where(PurchaseOrder.id == po_id)
        )
        .scalars()
        .first()
    )
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    items = []
    for it in (po.items or []):
        items.append(
            PurchaseOrderItemResponse(
                id=it.id,
                purchase_order_id=it.purchase_order_id,
                product_id=it.product_id,
                product_code=it.product.product_code if it.product else None,
                product_name=it.product.name if it.product else None,
                category=it.product.category if it.product else None,
                unit_of_measure=it.product.unit_of_measure if it.product else None,
                is_serialized=it.product.is_serialized if it.product else False,
                ordered_quantity=it.ordered_quantity,
                received_quantity=it.received_quantity,
                unit_price=it.unit_price,
                tax_rate_percent=it.tax_rate_percent,
                total_amount=it.total_amount,
                created_at=it.created_at,
            )
        )

    return PurchaseOrderDetailResponse(
        id=po.id,
        po_number=po.po_number,
        supplier_id=po.supplier_id,
        supplier_name=po.supplier.company_name if po.supplier else None,
        supplier_code=po.supplier.supplier_code if po.supplier else None,
        project_id=po.project_id,
        project_code=po.project.project_code if po.project else None,
        po_date=po.po_date,
        expected_delivery_date=po.expected_delivery_date,
        total_amount=po.total_amount,
        tax_amount=po.tax_amount,
        status=po.status,
        created_by=po.created_by,
        creator_name=po.creator.full_name if po.creator else None,
        notes=po.notes,
        items_count=len(items),
        created_at=po.created_at,
        updated_at=po.updated_at,
        items=items,
    )


# ==========================================
# 3. GOODS RECEIPT (GRN) ENDPOINTS
# ==========================================

@router.get("/goods-receipts", response_model=APIResponse[dict])
def list_goods_receipts(
    purchase_order_id: Optional[int] = Query(None, description="Filter by purchase order ID"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    search: Optional[str] = Query(None, description="Search by GRN number or challan number"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_procurement_read_access),
    db: Session = Depends(get_db),
):
    """
    List Goods Receipt Notes with pagination and filters.
    """
    query = (
        select(GoodsReceipt)
        .options(
            selectinload(GoodsReceipt.purchase_order),
            selectinload(GoodsReceipt.supplier),
            selectinload(GoodsReceipt.receiver),
            selectinload(GoodsReceipt.items),
        )
    )

    if purchase_order_id:
        query = query.where(GoodsReceipt.purchase_order_id == purchase_order_id)

    if supplier_id:
        query = query.where(GoodsReceipt.supplier_id == supplier_id)

    if search:
        s = f"%{search.strip()}%"
        query = query.where(
            or_(
                GoodsReceipt.grn_number.ilike(s),
                GoodsReceipt.challan_number.ilike(s),
            )
        )

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0

    receipts = (
        db.execute(
            query.order_by(GoodsReceipt.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    items = []
    for grn in receipts:
        items.append(
            GoodsReceiptResponse(
                id=grn.id,
                grn_number=grn.grn_number,
                purchase_order_id=grn.purchase_order_id,
                po_number=grn.purchase_order.po_number if grn.purchase_order else None,
                supplier_id=grn.supplier_id,
                supplier_name=grn.supplier.company_name if grn.supplier else None,
                received_date=grn.received_date,
                received_by=grn.received_by,
                receiver_name=grn.receiver.full_name if grn.receiver else None,
                challan_number=grn.challan_number,
                challan_date=grn.challan_date,
                status=grn.status,
                inspection_remarks=grn.inspection_remarks,
                items_count=len(grn.items) if grn.items else 0,
                created_at=grn.created_at,
            )
        )

    return APIResponse(
        message="Goods receipts retrieved successfully",
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        },
    )


@router.get("/goods-receipts/{grn_id}", response_model=APIResponse[GoodsReceiptDetailResponse])
def get_goods_receipt_detail(
    grn_id: int,
    current_user: User = Depends(require_procurement_read_access),
    db: Session = Depends(get_db),
):
    """
    Retrieve full details of a Goods Receipt Note including line inspection results.
    """
    grn = (
        db.execute(
            select(GoodsReceipt)
            .options(
                selectinload(GoodsReceipt.purchase_order),
                selectinload(GoodsReceipt.supplier),
                selectinload(GoodsReceipt.receiver),
                selectinload(GoodsReceipt.items).selectinload(GoodsReceiptItem.product),
            )
            .where(GoodsReceipt.id == grn_id)
        )
        .scalars()
        .first()
    )
    if not grn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goods receipt with ID {grn_id} not found",
        )

    items = []
    for it in (grn.items or []):
        items.append(
            GoodsReceiptItemResponse(
                id=it.id,
                goods_receipt_id=it.goods_receipt_id,
                po_item_id=it.po_item_id,
                product_id=it.product_id,
                product_code=it.product.product_code if it.product else None,
                product_name=it.product.name if it.product else None,
                received_quantity=it.received_quantity,
                accepted_quantity=it.accepted_quantity,
                rejected_quantity=it.rejected_quantity,
                rejection_reason=it.rejection_reason,
                created_at=it.created_at,
            )
        )

    detail = GoodsReceiptDetailResponse(
        id=grn.id,
        grn_number=grn.grn_number,
        purchase_order_id=grn.purchase_order_id,
        po_number=grn.purchase_order.po_number if grn.purchase_order else None,
        supplier_id=grn.supplier_id,
        supplier_name=grn.supplier.company_name if grn.supplier else None,
        received_date=grn.received_date,
        received_by=grn.received_by,
        receiver_name=grn.receiver.full_name if grn.receiver else None,
        challan_number=grn.challan_number,
        challan_date=grn.challan_date,
        status=grn.status,
        inspection_remarks=grn.inspection_remarks,
        items_count=len(items),
        created_at=grn.created_at,
        items=items,
    )

    return APIResponse(
        message="Goods receipt details retrieved successfully",
        data=detail,
    )


@router.get("/purchase-orders/{po_id}/goods-receipts", response_model=APIResponse[List[GoodsReceiptResponse]])
def get_po_goods_receipts(
    po_id: int,
    current_user: User = Depends(require_procurement_read_access),
    db: Session = Depends(get_db),
):
    """
    Get all Goods Receipt Notes recorded against a specific Purchase Order.
    """
    po = db.get(PurchaseOrder, po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    receipts = (
        db.execute(
            select(GoodsReceipt)
            .options(
                selectinload(GoodsReceipt.purchase_order),
                selectinload(GoodsReceipt.supplier),
                selectinload(GoodsReceipt.receiver),
                selectinload(GoodsReceipt.items),
            )
            .where(GoodsReceipt.purchase_order_id == po_id)
            .order_by(GoodsReceipt.created_at.desc())
        )
        .scalars()
        .all()
    )

    items = []
    for grn in receipts:
        items.append(
            GoodsReceiptResponse(
                id=grn.id,
                grn_number=grn.grn_number,
                purchase_order_id=grn.purchase_order_id,
                po_number=grn.purchase_order.po_number if grn.purchase_order else None,
                supplier_id=grn.supplier_id,
                supplier_name=grn.supplier.company_name if grn.supplier else None,
                received_date=grn.received_date,
                received_by=grn.received_by,
                receiver_name=grn.receiver.full_name if grn.receiver else None,
                challan_number=grn.challan_number,
                challan_date=grn.challan_date,
                status=grn.status,
                inspection_remarks=grn.inspection_remarks,
                items_count=len(grn.items) if grn.items else 0,
                created_at=grn.created_at,
            )
        )

    return APIResponse(
        message=f"Found {len(items)} goods receipts for PO '{po.po_number}'",
        data=items,
    )


@router.post("/goods-receipts", response_model=APIResponse[GoodsReceiptDetailResponse], status_code=status.HTTP_201_CREATED)
def record_goods_receipt(
    payload: GoodsReceiptCreate,
    current_user: User = Depends(require_procurement_manage_access),
    db: Session = Depends(get_db),
):
    """
    Record an inward physical goods receipt (GRN) and update inventory in one ACID transaction.
    - Validates PO is in ISSUED or PARTIALLY_RECEIVED.
    - Locks PO and PO items to prevent concurrent over-receipt.
    - Strictly rejects over-receipt (no tolerance).
    - Checks received = accepted + rejected.
    - Updates PO items received_quantity and recalculates PO status.
    - For accepted stock: upserts inventory, updates moving weighted average cost,
      records stock movement ledger, and registers serialized products.
    """
    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Goods receipt must contain at least one inspected item",
        )

    # 1. Row-lock Purchase Order
    po = db.execute(
        select(PurchaseOrder)
        .where(PurchaseOrder.id == payload.purchase_order_id)
        .with_for_update()
    ).scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID {payload.purchase_order_id} not found",
        )

    if po.status == "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot receive goods against a DRAFT purchase order '{po.po_number}'. Please issue the PO first.",
        )
    if po.status == "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot receive goods against CANCELLED purchase order '{po.po_number}'.",
        )
    if po.status == "RECEIVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Purchase order '{po.po_number}' is already fully received.",
        )

    # 2. Row-lock PO items
    po_items_db = db.execute(
        select(PurchaseOrderItem)
        .where(PurchaseOrderItem.purchase_order_id == po.id)
        .with_for_update()
    ).scalars().all()
    po_items_map = {item.id: item for item in po_items_db}

    # 3. Validate Line Inspections
    total_accepted_grn = Decimal("0.00")
    total_rejected_grn = Decimal("0.00")
    total_received_grn = Decimal("0.00")

    inspected_items_prepared = []

    for item_in in payload.items:
        if item_in.po_item_id not in po_items_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PO Item ID {item_in.po_item_id} does not belong to Purchase Order '{po.po_number}'",
            )
        po_item = po_items_map[item_in.po_item_id]

        if item_in.product_id != po_item.product_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product ID {item_in.product_id} does not match PO Item product ID {po_item.product_id}",
            )

        recv_qty = Decimal(str(item_in.received_quantity))
        acc_qty = Decimal(str(item_in.accepted_quantity))
        rej_qty = Decimal(str(item_in.rejected_quantity or "0.00"))

        if recv_qty < 0 or acc_qty < 0 or rej_qty < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Received, accepted, and rejected quantities must be non-negative",
            )

        # Database Check Constraint: received_quantity = accepted_quantity + rejected_quantity
        if recv_qty != (acc_qty + rej_qty):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"For product ID {item_in.product_id}, received quantity ({recv_qty}) must equal accepted ({acc_qty}) + rejected ({rej_qty})",
            )

        # Rejection reason validation
        if rej_qty > 0 and (not item_in.rejection_reason or not item_in.rejection_reason.strip()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A valid rejection reason is mandatory when rejected quantity ({rej_qty}) > 0",
            )

        # Over-receipt rejection: total accepted across all GRNs cannot exceed ordered quantity
        remaining_unreceived = po_item.ordered_quantity - po_item.received_quantity
        if acc_qty > remaining_unreceived:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Over-receipt rejected for product ID {item_in.product_id}. "
                    f"Attempted to accept {acc_qty}, but only {remaining_unreceived} remains unreceived on PO."
                ),
            )

        # Serialized product validation
        product = db.get(Product, item_in.product_id)
        if product and product.is_serialized:
            if acc_qty > 0:
                if acc_qty != int(acc_qty):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Serialized product '{product.name}' cannot have fractional accepted quantity ({acc_qty})",
                    )
                expected_count = int(acc_qty)
                serials = [s.strip() for s in (item_in.serial_numbers or []) if s and s.strip()]
                if len(serials) != expected_count:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Serialized product '{product.name}' requires exactly {expected_count} serial numbers, but {len(serials)} were provided",
                    )
                # Check duplicates in payload
                if len(set(serials)) != len(serials):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Duplicate serial numbers detected in payload for product '{product.name}'",
                    )
                # Check duplicates in DB
                existing_in_db = db.execute(
                    select(SerialNumber.serial_number).where(SerialNumber.serial_number.in_(serials))
                ).scalars().all()
                if existing_in_db:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Serial number(s) already registered in system: {', '.join(existing_in_db)}",
                    )
                inspected_items_prepared.append((item_in, po_item, product, recv_qty, acc_qty, rej_qty, serials))
            else:
                inspected_items_prepared.append((item_in, po_item, product, recv_qty, acc_qty, rej_qty, []))
        else:
            inspected_items_prepared.append((item_in, po_item, product, recv_qty, acc_qty, rej_qty, []))

        total_received_grn += recv_qty
        total_accepted_grn += acc_qty
        total_rejected_grn += rej_qty

    if total_received_grn <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Total received quantity on GRN must be greater than zero",
        )

    # 4. Generate GRN number
    grn_number = _generate_grn_number(db)

    # Determine GRN status
    if total_rejected_grn > 0 and total_accepted_grn > 0:
        grn_status = "PARTIALLY_ACCEPTED"
    elif total_rejected_grn > 0 and total_accepted_grn == 0:
        grn_status = "REJECTED"
    else:
        grn_status = "ACCEPTED"

    # 5. Create GoodsReceipt
    grn = GoodsReceipt(
        grn_number=grn_number,
        purchase_order_id=po.id,
        supplier_id=po.supplier_id,
        received_date=payload.received_date,
        received_by=current_user.id,
        challan_number=payload.challan_number.strip() if payload.challan_number else None,
        challan_date=payload.challan_date,
        status=grn_status,
        inspection_remarks=payload.inspection_remarks.strip() if payload.inspection_remarks else None,
    )
    db.add(grn)
    db.flush()  # Populates grn.id

    # 6. Process line items, stock updates, ledger movements, and serials
    for item_in, po_item, product, recv_qty, acc_qty, rej_qty, serials in inspected_items_prepared:
        grn_item = GoodsReceiptItem(
            goods_receipt_id=grn.id,
            po_item_id=po_item.id,
            product_id=product.id,
            received_quantity=recv_qty,
            accepted_quantity=acc_qty,
            rejected_quantity=rej_qty,
            rejection_reason=item_in.rejection_reason.strip() if rej_qty > 0 and item_in.rejection_reason else None,
        )
        db.add(grn_item)

        # Update PO Item received quantity by accepted amount
        po_item.received_quantity += acc_qty

        # Process inward stock ONLY if accepted_quantity > 0
        if acc_qty > 0:
            # Row-lock inventory
            inventory = db.execute(
                select(Inventory)
                .where(Inventory.product_id == product.id)
                .with_for_update()
            ).scalar_one_or_none()

            old_qoh = inventory.quantity_on_hand if inventory else Decimal("0.00")
            old_cost = inventory.average_unit_cost if inventory else Decimal("0.00")
            new_qoh = old_qoh + acc_qty
            po_price = po_item.unit_price

            # Moving weighted average cost calculation:
            if old_qoh == Decimal("0.00"):
                new_avg_cost = po_price
            else:
                new_avg_cost = ((old_qoh * old_cost) + (acc_qty * po_price)) / new_qoh
            new_avg_cost = round(new_avg_cost, 2)

            if inventory is None:
                inventory = Inventory(
                    product_id=product.id,
                    warehouse_location="MAIN_WAREHOUSE",
                    quantity_on_hand=new_qoh,
                    reserved_quantity=Decimal("0.00"),
                    quantity_available=new_qoh,
                    average_unit_cost=new_avg_cost,
                    reorder_level=product.min_stock_alert if product and product.min_stock_alert is not None else Decimal("5.00"),
                    last_restocked_at=func.now(),
                )
                db.add(inventory)
                db.flush()  # Populates inventory.id
            else:
                inventory.quantity_on_hand = new_qoh
                inventory.average_unit_cost = new_avg_cost
                # Identity: quantity_available = quantity_on_hand - reserved_quantity
                inventory.quantity_available = new_qoh - inventory.reserved_quantity
                inventory.last_restocked_at = func.now()

            # Record StockMovement ledger
            movement = StockMovement(
                inventory_id=inventory.id,
                product_id=product.id,
                movement_type="PURCHASE_RECEIPT",
                reference_type="GRN",
                reference_id=grn.id,
                quantity=acc_qty,
                unit_cost=po_price,
                quantity_before=old_qoh,
                quantity_after=new_qoh,
                performed_by=current_user.id,
                remarks=f"Inward GRN {grn.grn_number} for PO {po.po_number}",
            )
            db.add(movement)

            # Register serial numbers
            if serials:
                for s_str in serials:
                    sn = SerialNumber(
                        serial_number=s_str,
                        product_id=product.id,
                        inventory_id=inventory.id,
                        purchase_order_id=po.id,
                        project_id=po.project_id,
                        supplier_id=po.supplier_id,
                        status="IN_STOCK",
                        warranty_months=60,
                        received_date=payload.received_date,
                    )
                    db.add(sn)

    # 7. Recalculate Purchase Order status
    all_ordered_received = True
    any_received = False
    for item in po_items_map.values():
        if item.received_quantity < item.ordered_quantity:
            all_ordered_received = False
        if item.received_quantity > 0:
            any_received = True

    if all_ordered_received:
        po.status = "RECEIVED"
    elif any_received:
        po.status = "PARTIALLY_RECEIVED"

    # Commit the atomic transaction
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Database integrity conflict during goods receipt processing: {str(e.orig)}",
        )

    _record_audit_log(
        db=db,
        user_id=current_user.id,
        action="GRN_RECEIPT",
        entity_name="GOODS_RECEIPT",
        entity_id=grn.id,
        details={
            "grn_number": grn.grn_number,
            "po_number": po.po_number,
            "accepted_qty": float(total_accepted_grn),
            "rejected_qty": float(total_rejected_grn),
            "po_new_status": po.status,
        },
    )
    db.commit()

    return APIResponse(
        message=f"Goods Receipt Note '{grn.grn_number}' recorded and warehouse inventory updated successfully",
        data=_build_grn_detail_response(db, grn.id),
    )


def _build_grn_detail_response(db: Session, grn_id: int) -> GoodsReceiptDetailResponse:
    grn = (
        db.execute(
            select(GoodsReceipt)
            .options(
                selectinload(GoodsReceipt.purchase_order),
                selectinload(GoodsReceipt.supplier),
                selectinload(GoodsReceipt.receiver),
                selectinload(GoodsReceipt.items).selectinload(GoodsReceiptItem.product),
            )
            .where(GoodsReceipt.id == grn_id)
        )
        .scalars()
        .first()
    )
    if not grn:
        raise HTTPException(status_code=404, detail="Goods receipt not found")

    items = []
    for it in (grn.items or []):
        items.append(
            GoodsReceiptItemResponse(
                id=it.id,
                goods_receipt_id=it.goods_receipt_id,
                po_item_id=it.po_item_id,
                product_id=it.product_id,
                product_code=it.product.product_code if it.product else None,
                product_name=it.product.name if it.product else None,
                received_quantity=it.received_quantity,
                accepted_quantity=it.accepted_quantity,
                rejected_quantity=it.rejected_quantity,
                rejection_reason=it.rejection_reason,
                created_at=it.created_at,
            )
        )

    return GoodsReceiptDetailResponse(
        id=grn.id,
        grn_number=grn.grn_number,
        purchase_order_id=grn.purchase_order_id,
        po_number=grn.purchase_order.po_number if grn.purchase_order else None,
        supplier_id=grn.supplier_id,
        supplier_name=grn.supplier.company_name if grn.supplier else None,
        received_date=grn.received_date,
        received_by=grn.received_by,
        receiver_name=grn.receiver.full_name if grn.receiver else None,
        challan_number=grn.challan_number,
        challan_date=grn.challan_date,
        status=grn.status,
        inspection_remarks=grn.inspection_remarks,
        items_count=len(items),
        created_at=grn.created_at,
        items=items,
    )


# ==========================================
# 4. INVENTORY & STOCK LEDGER ENDPOINTS
# ==========================================

@router.get("/inventory", response_model=APIResponse[dict])
def list_warehouse_inventory(
    search: Optional[str] = Query(None, description="Search product name, code, brand"),
    category: Optional[str] = Query(None, description="Filter product category"),
    low_stock_only: Optional[bool] = Query(False, description="Filter items at or below reorder level"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_inventory_read_access),
    db: Session = Depends(get_db),
):
    """
    List inventory stock levels with weighted average cost, valuation, and low-stock alerts.
    """
    query = (
        select(Inventory)
        .join(Product, Inventory.product_id == Product.id)
        .options(selectinload(Inventory.product))
    )

    if search:
        s = f"%{search.strip()}%"
        query = query.where(
            or_(
                Product.name.ilike(s),
                Product.product_code.ilike(s),
                Product.brand.ilike(s),
                Product.model_number.ilike(s),
            )
        )

    if category:
        query = query.where(Product.category == category.strip().upper())

    if low_stock_only:
        query = query.where(Inventory.quantity_on_hand <= Inventory.reorder_level)

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0

    inv_rows = (
        db.execute(
            query.order_by(Product.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    items = []
    for inv in inv_rows:
        p = inv.product
        qoh = inv.quantity_on_hand
        cost = inv.average_unit_cost
        is_low = qoh <= inv.reorder_level
        val = round(qoh * cost, 2)

        items.append(
            InventoryItemResponse(
                id=inv.id,
                product_id=inv.product_id,
                product_code=p.product_code if p else "",
                product_name=p.name if p else "",
                category=p.category if p else "",
                brand=p.brand if p else None,
                model_number=p.model_number if p else None,
                unit_of_measure=p.unit_of_measure if p else "NOS",
                is_serialized=p.is_serialized if p else False,
                warehouse_location=inv.warehouse_location,
                quantity_on_hand=inv.quantity_on_hand,
                reserved_quantity=inv.reserved_quantity,
                quantity_available=inv.quantity_available,
                average_unit_cost=inv.average_unit_cost,
                reorder_level=inv.reorder_level,
                is_low_stock=is_low,
                total_valuation=val,
                last_restocked_at=inv.last_restocked_at,
                created_at=inv.created_at,
                updated_at=inv.updated_at,
            )
        )

    # High-level summary across all warehouse records
    summary_data = db.execute(
        select(
            func.count(Inventory.id),
            func.coalesce(func.sum(Inventory.quantity_on_hand * Inventory.average_unit_cost), Decimal("0.00")),
            func.count(func.nullif(Inventory.quantity_on_hand > Inventory.reorder_level, True)),
        )
    ).first()

    total_records = summary_data[0] if summary_data else 0
    total_valuation_all = summary_data[1] if summary_data else Decimal("0.00")
    total_low_stock_all = summary_data[2] if summary_data else 0

    return APIResponse(
        message="Warehouse inventory retrieved successfully",
        data={
            "items": items,
            "summary": {
                "total_tracked_products": total_records,
                "total_valuation": total_valuation_all,
                "low_stock_count": total_low_stock_all,
            },
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        },
    )


@router.get("/inventory/{product_id}/movements", response_model=APIResponse[dict])
def get_product_stock_movements(
    product_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_inventory_read_access),
    db: Session = Depends(get_db),
):
    """
    Get audit ledger of stock movements for a specific product.
    """
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    query = (
        select(StockMovement)
        .options(selectinload(StockMovement.performer))
        .where(StockMovement.product_id == product_id)
    )

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0

    movements = (
        db.execute(
            query.order_by(StockMovement.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    items = []
    for sm in movements:
        items.append(
            StockMovementResponse(
                id=sm.id,
                inventory_id=sm.inventory_id,
                product_id=sm.product_id,
                product_code=product.product_code,
                product_name=product.name,
                movement_type=sm.movement_type,
                reference_type=sm.reference_type,
                reference_id=sm.reference_id,
                quantity=sm.quantity,
                unit_cost=sm.unit_cost,
                quantity_before=sm.quantity_before,
                quantity_after=sm.quantity_after,
                performed_by=sm.performed_by,
                performer_name=sm.performer.full_name if sm.performer else None,
                remarks=sm.remarks,
                created_at=sm.created_at,
            )
        )

    return APIResponse(
        message=f"Stock movements for '{product.name}' retrieved successfully",
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        },
    )


@router.get("/inventory/{product_id}/serials", response_model=APIResponse[dict])
def get_product_serials(
    product_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_serials_read_access),
    db: Session = Depends(get_db),
):
    """
    Get serial numbers for a serialized product with lifecycle status.
    """
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    query = (
        select(SerialNumber)
        .options(
            selectinload(SerialNumber.product),
            selectinload(SerialNumber.project),
        )
        .where(SerialNumber.product_id == product_id)
    )

    if status_filter:
        query = query.where(SerialNumber.status == status_filter.strip().upper())

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar() or 0

    serials = (
        db.execute(
            query.order_by(SerialNumber.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    items = []
    for sn in serials:
        items.append(
            SerialNumberResponse(
                id=sn.id,
                serial_number=sn.serial_number,
                product_id=sn.product_id,
                product_code=product.product_code,
                product_name=product.name,
                inventory_id=sn.inventory_id,
                purchase_order_id=sn.purchase_order_id,
                project_id=sn.project_id,
                project_code=sn.project.project_code if sn.project else None,
                supplier_id=sn.supplier_id,
                status=sn.status,
                warranty_months=sn.warranty_months,
                received_date=sn.received_date,
                created_at=sn.created_at,
                updated_at=sn.updated_at,
            )
        )

    return APIResponse(
        message=f"Serial numbers for '{product.name}' retrieved successfully",
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        },
    )


# ==========================================
# 5. PROJECT MATERIAL SHORTAGE VIEW
# ==========================================

@router.get("/inventory/project-shortages/{project_id}", response_model=APIResponse[ProjectMaterialShortageResponse])
def get_project_material_shortages(
    project_id: int,
    current_user: User = Depends(require_procurement_read_access),
    db: Session = Depends(get_db),
):
    """
    Read-only view comparing Project BOM item planned/allocated quantities against
    authoritative warehouse available stock, to guide project-specific PO creation.
    """
    project = (
        db.execute(
            select(Project)
            .options(
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
    shortage_count = 0

    for bom_item in (project.bom_items or []):
        p = bom_item.product
        inv = db.execute(
            select(Inventory).where(Inventory.product_id == bom_item.product_id)
        ).scalar_one_or_none()

        qoh = inv.quantity_on_hand if inv else Decimal("0.00")
        avail = inv.quantity_available if inv else Decimal("0.00")

        planned = bom_item.planned_quantity
        allocated = bom_item.allocated_quantity
        unallocated = max(Decimal("0.00"), planned - allocated)

        # Shortage = unallocated required minus available warehouse stock
        shortage = max(Decimal("0.00"), unallocated - avail)
        has_shortage = shortage > Decimal("0.00")
        if has_shortage:
            shortage_count += 1

        items.append(
            ProjectMaterialShortageItem(
                bom_item_id=bom_item.id,
                product_id=bom_item.product_id,
                product_code=p.product_code if p else "",
                product_name=p.name if p else "",
                category=p.category if p else bom_item.item_category,
                unit_of_measure=p.unit_of_measure if p else "NOS",
                planned_quantity=planned,
                allocated_quantity=allocated,
                unallocated_quantity=unallocated,
                quantity_on_hand=qoh,
                quantity_available=avail,
                shortage_quantity=shortage,
                has_shortage=has_shortage,
            )
        )

    resp = ProjectMaterialShortageResponse(
        project_id=project.id,
        project_code=project.project_code,
        system_capacity_kw=project.system_capacity_kw,
        system_type=project.system_type,
        total_bom_items=len(items),
        shortage_items_count=shortage_count,
        items=items,
    )

    return APIResponse(
        message=f"Material shortages for project '{project.project_code}' calculated successfully",
        data=resp,
    )
