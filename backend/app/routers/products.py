from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
import math

from app.database import get_db
from app.models.crm import Product
from app.models.auth import User
from app.models.workflow import AuditLog
from app.schemas.products import (
    ProductCreate,
    ProductUpdate,
    ProductStatusUpdate,
    ProductResponse,
    ProductListResponse,
    VALID_PRODUCT_CATEGORIES,
)
from app.schemas import APIResponse
from app.dependencies.auth import get_current_user, get_user_permissions
from app.utils.roles import SystemRole

router = APIRouter(prefix="/products", tags=["Product Catalog"])


# ==========================================
# INTERNAL HELPERS & AUTHORIZATION
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
        entity_name="PRODUCT",
        entity_id=entity_id,
        details=details or {},
    )
    db.add(log)


def _build_product_response(p: Product) -> ProductResponse:
    return ProductResponse(
        id=p.id,
        product_code=p.product_code,
        name=p.name,
        category=p.category,
        brand=p.brand,
        model_number=p.model_number,
        wattage_or_capacity=p.wattage_or_capacity,
        unit_of_measure=p.unit_of_measure,
        is_serialized=p.is_serialized,
        base_price=float(p.base_price) if p.base_price is not None else 0.0,
        tax_rate_percent=float(p.tax_rate_percent) if p.tax_rate_percent is not None else 12.0,
        min_stock_alert=float(p.min_stock_alert) if p.min_stock_alert is not None else 5.0,
        is_active=p.is_active,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def require_product_read_access(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure user has read permission for the product catalog.
    SUPER_ADMIN has universal access.
    CUSTOMER is strictly forbidden.
    Other roles require 'products.read', 'bom.read', 'inventory.read', or 'quotations.read'.
    """
    if current_user.role and current_user.role.slug == SystemRole.SUPER_ADMIN:
        return current_user

    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers cannot access internal product catalog",
        )

    user_perms = get_user_permissions(current_user)
    if (
        "products.read" in user_perms
        or "bom.read" in user_perms
        or "inventory.read" in user_perms
        or "quotations.read" in user_perms
    ):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Missing required permission: products.read",
    )


def require_product_create_access(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure user has permission to add new products to the catalog.
    SUPER_ADMIN has full access.
    CUSTOMER and FIELD_TECHNICIAN are strictly forbidden.
    Other roles require 'products.create', 'bom.manage', or 'inventory.manage'.
    """
    if current_user.role and current_user.role.slug == SystemRole.SUPER_ADMIN:
        return current_user

    if current_user.role and current_user.role.slug in (SystemRole.CUSTOMER, SystemRole.FIELD_TECHNICIAN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role privileges to create catalog products",
        )

    user_perms = get_user_permissions(current_user)
    if (
        "products.create" in user_perms
        or "bom.manage" in user_perms
        or "inventory.manage" in user_perms
    ):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Missing required permission: products.create",
    )


def require_product_update_access(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensure user has permission to modify existing products or alter active status.
    SUPER_ADMIN has full access.
    CUSTOMER and FIELD_TECHNICIAN are strictly forbidden.
    Other roles require 'products.update', 'bom.manage', or 'inventory.manage'.
    """
    if current_user.role and current_user.role.slug == SystemRole.SUPER_ADMIN:
        return current_user

    if current_user.role and current_user.role.slug in (SystemRole.CUSTOMER, SystemRole.FIELD_TECHNICIAN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role privileges to update catalog products",
        )

    user_perms = get_user_permissions(current_user)
    if (
        "products.update" in user_perms
        or "bom.manage" in user_perms
        or "inventory.manage" in user_perms
    ):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Missing required permission: products.update",
    )


# ==========================================
# ENDPOINTS
# ==========================================

@router.post("", response_model=APIResponse[ProductResponse], status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_product_create_access),
):
    """
    Create a new product/equipment record in the master catalog.
    Validates product code uniqueness, categories, and non-negative pricing.
    """
    # Check for duplicate product_code (case-insensitive)
    existing = db.execute(
        select(Product).where(func.lower(Product.product_code) == payload.product_code.lower())
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with code '{payload.product_code}' already exists",
        )

    product = Product(
        product_code=payload.product_code,
        name=payload.name,
        category=payload.category,
        brand=payload.brand,
        model_number=payload.model_number,
        wattage_or_capacity=payload.wattage_or_capacity,
        unit_of_measure=payload.unit_of_measure,
        is_serialized=payload.is_serialized,
        base_price=payload.base_price,
        tax_rate_percent=payload.tax_rate_percent,
        min_stock_alert=payload.min_stock_alert,
        is_active=payload.is_active,
    )

    db.add(product)
    try:
        db.commit()
        db.refresh(product)
    except IntegrityError as exc:
        db.rollback()
        err_str = str(exc).lower()
        if "product_code" in err_str or "unique" in err_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product code '{payload.product_code}' already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity violation: {str(exc.orig) if hasattr(exc, 'orig') else str(exc)}",
        )

    _record_audit_log(
        db,
        user_id=current_user.id,
        action="CREATE",
        entity_id=product.id,
        details={
            "product_code": product.product_code,
            "category": product.category,
            "base_price": float(product.base_price),
        },
    )
    db.commit()

    return APIResponse(
        success=True,
        message=f"Product '{product.name}' created successfully",
        data=_build_product_response(product),
    )


@router.get("", response_model=APIResponse[ProductListResponse])
def list_products(
    search: Optional[str] = Query(None, description="Search by product code, name, brand, or model number"),
    category: Optional[str] = Query(None, description="Filter by category (e.g. SOLAR_PANEL, INVERTER)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status (true/false)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_product_read_access),
):
    """
    List products with pagination, search, category filtering, and active status filtering.
    """
    stmt = select(Product)

    if category:
        clean_cat = category.strip().upper()
        stmt = stmt.where(func.upper(Product.category) == clean_cat)

    if is_active is not None:
        stmt = stmt.where(Product.is_active == is_active)

    if search:
        term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Product.product_code).like(term),
                func.lower(Product.name).like(term),
                func.lower(Product.brand).like(term),
                func.lower(Product.model_number).like(term),
            )
        )

    # Count total matching
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar() or 0

    # Pagination & sorting
    stmt = stmt.order_by(Product.category.asc(), Product.name.asc()).offset((page - 1) * limit).limit(limit)
    products = db.execute(stmt).scalars().all()

    items = [_build_product_response(p) for p in products]
    total_pages = math.ceil(total / limit) if total > 0 else 1

    return APIResponse(
        success=True,
        message="Products retrieved successfully",
        data=ProductListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        ),
    )


@router.get("/{product_id}", response_model=APIResponse[ProductResponse])
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_product_read_access),
):
    """
    Retrieve single product details by ID.
    """
    product = db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    return APIResponse(
        success=True,
        message="Product details retrieved successfully",
        data=_build_product_response(product),
    )


@router.put("/{product_id}", response_model=APIResponse[ProductResponse])
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_product_update_access),
):
    """
    Update product catalog information, prices, tax rate, or active status.
    Historical quotation and BOM records referencing this product remain unaffected.
    """
    product = db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    # If product_code is changing, ensure uniqueness
    if payload.product_code and payload.product_code.lower() != product.product_code.lower():
        code_conflict = db.execute(
            select(Product.id).where(
                func.lower(Product.product_code) == payload.product_code.lower(),
                Product.id != product.id,
            )
        ).scalar_one_or_none()
        if code_conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with code '{payload.product_code}' already exists",
            )
        product.product_code = payload.product_code

    # Apply updates
    if payload.name is not None:
        product.name = payload.name
    if payload.category is not None:
        product.category = payload.category
    if payload.brand is not None:
        product.brand = payload.brand
    if payload.model_number is not None:
        product.model_number = payload.model_number
    if payload.wattage_or_capacity is not None:
        product.wattage_or_capacity = payload.wattage_or_capacity
    if payload.unit_of_measure is not None:
        product.unit_of_measure = payload.unit_of_measure
    if payload.is_serialized is not None:
        product.is_serialized = payload.is_serialized
    if payload.base_price is not None:
        product.base_price = payload.base_price
    if payload.tax_rate_percent is not None:
        product.tax_rate_percent = payload.tax_rate_percent
    if payload.min_stock_alert is not None:
        product.min_stock_alert = payload.min_stock_alert
    if payload.is_active is not None:
        product.is_active = payload.is_active

    product.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(product)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database update error: {str(exc.orig) if hasattr(exc, 'orig') else str(exc)}",
        )

    _record_audit_log(
        db,
        user_id=current_user.id,
        action="UPDATE",
        entity_id=product.id,
        details={"product_code": product.product_code, "is_active": product.is_active},
    )
    db.commit()

    return APIResponse(
        success=True,
        message=f"Product '{product.product_code}' updated successfully",
        data=_build_product_response(product),
    )


@router.patch("/{product_id}/status", response_model=APIResponse[ProductResponse])
def update_product_status(
    product_id: int,
    payload: ProductStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_product_update_access),
):
    """
    Activate or deactivate a product without physically deleting the database record.
    Preserves historical relationships in BOMs, quotations, purchase orders, and inventory.
    """
    product = db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    product.is_active = payload.is_active
    product.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(product)

    action_label = "ACTIVATE" if payload.is_active else "DEACTIVATE"
    _record_audit_log(
        db,
        user_id=current_user.id,
        action=action_label,
        entity_id=product.id,
        details={"is_active": product.is_active},
    )
    db.commit()

    status_str = "activated" if product.is_active else "deactivated"
    return APIResponse(
        success=True,
        message=f"Product '{product.product_code}' has been {status_str}",
        data=_build_product_response(product),
    )
