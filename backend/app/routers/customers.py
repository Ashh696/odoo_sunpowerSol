from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_
from datetime import datetime, timezone
import math

from app.database import get_db
from app.models.crm import Customer, Enquiry
from app.models.auth import User
from app.schemas.crm import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
)
from app.schemas import APIResponse
from app.dependencies.auth import get_current_user, require_permissions
from app.utils.roles import SystemRole

router = APIRouter(prefix="/customers", tags=["Customer Management"])


def _build_customer_response(c: Customer, db: Session) -> CustomerResponse:
    # Compute enquiry count
    enq_count = db.execute(
        select(func.count(Enquiry.id)).where(Enquiry.customer_id == c.id)
    ).scalar() or 0

    creator_name = None
    if c.creator:
        creator_name = c.creator.full_name

    cust_type = c.customer_type
    if cust_type and cust_type.strip().upper() == "INDIVIDUAL":
        cust_type = "RESIDENTIAL"

    return CustomerResponse(
        id=c.id,
        user_id=c.user_id,
        customer_type=cust_type,
        full_name=c.full_name,
        email=c.email,
        phone=c.phone,
        alternate_phone=c.alternate_phone,
        address=c.address,
        city=c.city,
        state=c.state,
        pincode=c.pincode,
        electricity_consumer_number=c.electricity_consumer_number,
        sanctioned_load_kw=float(c.sanctioned_load_kw) if c.sanctioned_load_kw is not None else None,
        created_by=c.created_by,
        creator_name=creator_name,
        is_active=c.is_active,
        enquiry_count=enq_count,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.get("", response_model=APIResponse[CustomerListResponse])
def list_customers(
    search: Optional[str] = Query(None, description="Search by name, phone, email, city, or consumer number"),
    customer_type: Optional[str] = Query(None, description="Filter by customer type (RESIDENTIAL, COMMERCIAL, INDUSTRIAL)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("customers.read")),
):
    """
    List customers with search, filtering, and pagination.
    Restricted to internal roles with 'customers.read'.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer accounts cannot access the internal customer directory",
        )

    stmt = select(Customer).options(selectinload(Customer.creator))

    if search:
        term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Customer.full_name).like(term),
                func.lower(Customer.phone).like(term),
                func.coalesce(func.lower(Customer.email), "").like(term),
                func.lower(Customer.city).like(term),
                func.coalesce(func.lower(Customer.electricity_consumer_number), "").like(term),
            )
        )

    if customer_type:
        c_type = customer_type.strip().upper()
        if c_type == "RESIDENTIAL":
            stmt = stmt.where(Customer.customer_type.in_(["RESIDENTIAL", "INDIVIDUAL"]))
        else:
            stmt = stmt.where(Customer.customer_type == c_type)

    if is_active is not None:
        stmt = stmt.where(Customer.is_active == is_active)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar() or 0

    # Paginate and order by newest first
    stmt = stmt.order_by(Customer.created_at.desc()).offset((page - 1) * limit).limit(limit)
    customers = db.execute(stmt).scalars().all()

    items = [_build_customer_response(c, db) for c in customers]
    total_pages = math.ceil(total / limit) if total > 0 else 1

    return APIResponse(
        success=True,
        message="Customers retrieved successfully",
        data=CustomerListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        ),
    )


@router.post("", response_model=APIResponse[CustomerResponse], status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("customers.create")),
):
    """
    Register a new customer.
    Checks for potential duplicate phone or electricity consumer number.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer accounts cannot register internal customer records",
        )

    clean_phone = payload.phone.strip()
    clean_email = payload.email.strip().lower() if payload.email else None
    clean_consumer_no = payload.electricity_consumer_number.strip() if payload.electricity_consumer_number else None

    # Check duplicate phone
    existing_phone = db.execute(
        select(Customer).where(Customer.phone == clean_phone)
    ).scalar_one_or_none()
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A customer with phone number '{clean_phone}' is already registered (Customer ID: {existing_phone.id}, Name: {existing_phone.full_name})",
        )

    # Check duplicate electricity consumer number if provided
    if clean_consumer_no:
        existing_consumer = db.execute(
            select(Customer).where(Customer.electricity_consumer_number == clean_consumer_no)
        ).scalar_one_or_none()
        if existing_consumer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A customer with electricity consumer number '{clean_consumer_no}' already exists (Customer ID: {existing_consumer.id})",
            )

    customer = Customer(
        customer_type=payload.customer_type,
        full_name=payload.full_name.strip(),
        email=clean_email,
        phone=clean_phone,
        alternate_phone=payload.alternate_phone.strip() if payload.alternate_phone else None,
        address=payload.address.strip(),
        city=payload.city.strip(),
        state=payload.state.strip(),
        pincode=payload.pincode.strip(),
        electricity_consumer_number=clean_consumer_no,
        sanctioned_load_kw=payload.sanctioned_load_kw,
        created_by=current_user.id,
        is_active=True,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    # Eager load creator
    customer = db.execute(
        select(Customer).where(Customer.id == customer.id).options(selectinload(Customer.creator))
    ).scalar_one()

    return APIResponse(
        success=True,
        message="Customer registered successfully",
        data=_build_customer_response(customer, db),
    )


@router.get("/me", response_model=APIResponse[CustomerResponse])
def get_my_customer_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get customer profile linked to the currently authenticated user.
    """
    cust_record = db.execute(
        select(Customer)
        .where(Customer.user_id == current_user.id)
        .options(selectinload(Customer.creator))
    ).scalar_one_or_none()

    if not cust_record and current_user.email:
        # Check if customer record exists with matching email or phone
        cust_record = db.execute(
            select(Customer)
            .where(
                or_(
                    func.lower(Customer.email) == current_user.email.lower().strip(),
                    Customer.phone == current_user.phone,
                )
            )
            .options(selectinload(Customer.creator))
        ).scalars().first()
        if cust_record and not cust_record.user_id:
            cust_record.user_id = current_user.id
            db.commit()
            db.refresh(cust_record)

    if not cust_record and current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        # Auto-provision a default Customer profile for valid authenticated customer user
        cust_record = Customer(
            user_id=current_user.id,
            customer_type="RESIDENTIAL",
            full_name=current_user.full_name or "Solar Customer",
            email=current_user.email,
            phone=current_user.phone or "9876543210",
            address="Solar Rooftop Residence",
            city="Hyderabad",
            state="Telangana",
            pincode="500001",
            created_by=current_user.id,
            is_active=True,
        )
        db.add(cust_record)
        db.commit()
        db.refresh(cust_record)

    if not cust_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No customer profile associated with the current user account",
        )
    return APIResponse(
        success=True,
        message="Customer profile retrieved successfully",
        data=_build_customer_response(cust_record, db),
    )


@router.put("/me", response_model=APIResponse[CustomerResponse])
def update_my_customer_profile(
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update profile contact and site details for the authenticated customer.
    Customers cannot modify user_id, customer_type, is_active, or records belonging to other customers.
    """
    cust_record = db.execute(
        select(Customer)
        .where(Customer.user_id == current_user.id)
        .options(selectinload(Customer.creator))
    ).scalar_one_or_none()

    if not cust_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No customer profile associated with the current user account",
        )

    if payload.full_name is not None and payload.full_name.strip():
        cust_record.full_name = payload.full_name.strip()
    if payload.alternate_phone is not None:
        cust_record.alternate_phone = payload.alternate_phone.strip() if payload.alternate_phone else None
    if payload.address is not None:
        cust_record.address = payload.address.strip()
    if payload.city is not None:
        cust_record.city = payload.city.strip()
    if payload.state is not None:
        cust_record.state = payload.state.strip()
    if payload.pincode is not None:
        cust_record.pincode = payload.pincode.strip()

    if payload.electricity_consumer_number is not None:
        clean_consumer = payload.electricity_consumer_number.strip() if payload.electricity_consumer_number else None
        if clean_consumer and clean_consumer != cust_record.electricity_consumer_number:
            dup_cons = db.execute(
                select(Customer).where(
                    Customer.electricity_consumer_number == clean_consumer,
                    Customer.id != cust_record.id,
                )
            ).scalar_one_or_none()
            if dup_cons:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Consumer number '{clean_consumer}' already registered with another customer",
                )
        cust_record.electricity_consumer_number = clean_consumer

    cust_record.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(cust_record)

    return APIResponse(
        success=True,
        message="Customer profile updated successfully",
        data=_build_customer_response(cust_record, db),
    )


@router.get("/{customer_id}", response_model=APIResponse[CustomerResponse])
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("customers.read")),
):
    """
    Get customer details by ID.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        # If user is a customer, verify if this customer record is linked to them
        cust_record = db.execute(
            select(Customer).where(Customer.id == customer_id, Customer.user_id == current_user.id)
        ).scalar_one_or_none()
        if not cust_record:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this customer record",
            )
        return APIResponse(
            success=True,
            message="Customer retrieved successfully",
            data=_build_customer_response(cust_record, db),
        )

    customer = db.execute(
        select(Customer).where(Customer.id == customer_id).options(selectinload(Customer.creator))
    ).scalar_one_or_none()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found",
        )

    return APIResponse(
        success=True,
        message="Customer retrieved successfully",
        data=_build_customer_response(customer, db),
    )


@router.put("/{customer_id}", response_model=APIResponse[CustomerResponse])
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("customers.update")),
):
    """
    Update existing customer details.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer accounts cannot edit internal customer records",
        )

    customer = db.execute(
        select(Customer).where(Customer.id == customer_id).options(selectinload(Customer.creator))
    ).scalar_one_or_none()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found",
        )

    # Validate duplicate phone if changing
    if payload.phone is not None:
        clean_phone = payload.phone.strip()
        if clean_phone != customer.phone:
            dup_phone = db.execute(
                select(Customer).where(Customer.phone == clean_phone, Customer.id != customer_id)
            ).scalar_one_or_none()
            if dup_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Phone number '{clean_phone}' is already registered with another customer (ID: {dup_phone.id})",
                )
            customer.phone = clean_phone

    # Validate duplicate consumer number if changing
    if payload.electricity_consumer_number is not None:
        clean_consumer = payload.electricity_consumer_number.strip() if payload.electricity_consumer_number else None
        if clean_consumer and clean_consumer != customer.electricity_consumer_number:
            dup_cons = db.execute(
                select(Customer).where(
                    Customer.electricity_consumer_number == clean_consumer,
                    Customer.id != customer_id,
                )
            ).scalar_one_or_none()
            if dup_cons:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Consumer number '{clean_consumer}' already registered with another customer (ID: {dup_cons.id})",
                )
        customer.electricity_consumer_number = clean_consumer

    if payload.customer_type is not None:
        customer.customer_type = payload.customer_type
    if payload.full_name is not None:
        customer.full_name = payload.full_name.strip()
    if payload.email is not None:
        customer.email = payload.email.strip().lower() if payload.email else None
    if payload.alternate_phone is not None:
        customer.alternate_phone = payload.alternate_phone.strip() if payload.alternate_phone else None
    if payload.address is not None:
        customer.address = payload.address.strip()
    if payload.city is not None:
        customer.city = payload.city.strip()
    if payload.state is not None:
        customer.state = payload.state.strip()
    if payload.pincode is not None:
        customer.pincode = payload.pincode.strip()
    if payload.sanctioned_load_kw is not None:
        customer.sanctioned_load_kw = payload.sanctioned_load_kw
    if payload.is_active is not None:
        customer.is_active = payload.is_active

    customer.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(customer)

    return APIResponse(
        success=True,
        message="Customer updated successfully",
        data=_build_customer_response(customer, db),
    )
