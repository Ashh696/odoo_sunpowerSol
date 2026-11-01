from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_
from datetime import datetime, timezone
import re

from app.database import get_db
from app.models.auth import User, Role, RolePermission
from app.models.crm import Customer
from app.utils.roles import SystemRole
from app.schemas import (
    APIResponse,
    LoginRequest,
    TokenResponse,
    UserProfileResponse,
    RoleInfo,
    ChangePasswordRequest,
    CustomerRegisterRequest,
)
from app.utils.security import (
    verify_password,
    hash_password,
    create_access_token,
)
from app.config import settings
from app.dependencies import get_current_user, get_user_permissions
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def build_user_profile(user: User) -> UserProfileResponse:
    """Helper to convert a User model into a sanitized UserProfileResponse."""
    permissions = sorted(list(get_user_permissions(user)))
    role_info = RoleInfo(
        id=user.role.id,
        name=user.role.name,
        slug=user.role.slug,
        description=user.role.description,
    )
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        phone=user.phone,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
        last_login_at=user.last_login_at,
        role=role_info,
        permissions=permissions,
    )


@router.post("/login", response_model=APIResponse[TokenResponse])
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user via email and password, issuing a signed JWT access token.
    """
    clean_email = request.email.lower().strip()

    stmt = (
        select(User)
        .where(User.email == clean_email)
        .options(
            selectinload(User.role).selectinload(Role.role_permissions).selectinload(RolePermission.permission)
        )
    )
    user = db.execute(stmt).scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        logger.warning(f"Failed login attempt for email: {clean_email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning(f"Inactive user login attempt: {clean_email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact administrator.",
        )

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    # Generate JWT token
    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.slug if user.role else None,
    }
    access_token = create_access_token(data=token_payload)

    user_profile = build_user_profile(user)

    token_data = TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=user_profile,
    )

    return APIResponse(
        success=True,
        message="Login successful",
        data=token_data,
    )


@router.get("/me", response_model=APIResponse[UserProfileResponse])
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Retrieve profile details, assigned role, and permissions of the authenticated user.
    """
    profile = build_user_profile(current_user)
    return APIResponse(
        success=True,
        message="User profile retrieved",
        data=profile,
    )


@router.post("/change-password", response_model=APIResponse[dict])
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change password for the currently authenticated user.
    """
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed",
        )

    if request.current_password == request.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long",
        )

    # Hash and save new password
    current_user.hashed_password = hash_password(request.new_password)
    db.commit()

    logger.info(f"Password changed successfully for user_id={current_user.id}")

    return APIResponse(
        success=True,
        message="Password updated successfully. Please use your new password for subsequent logins.",
        data={"user_id": current_user.id},
    )


@router.post("/register", response_model=APIResponse[TokenResponse], status_code=status.HTTP_201_CREATED)
def register_customer(request: CustomerRegisterRequest, db: Session = Depends(get_db)):
    """
    Public customer self-registration endpoint.
    Strictly restricted to registering accounts with the canonical CUSTOMER role.
    Employee registration is strictly prohibited through this endpoint.
    """
    clean_email = str(request.email).lower().strip()
    clean_phone = request.phone.strip()
    full_name = request.full_name.strip()

    # Validate phone digit count
    digits_only = re.sub(r"[^\d]", "", clean_phone)
    if len(digits_only) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mobile phone number must contain at least 10 digits.",
        )

    # Validate password minimum length
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long.",
        )

    # Check for existing user account by email or phone
    existing_user = db.execute(
        select(User).where(
            or_(
                func.lower(User.email) == clean_email,
                User.phone == clean_phone,
            )
        )
    ).scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address or phone number already exists. Please sign in.",
        )

    # Retrieve canonical CUSTOMER role (enforced on backend, client role input is impossible)
    customer_role = db.execute(
        select(Role).where(Role.slug == SystemRole.CUSTOMER)
    ).scalar_one_or_none()

    if not customer_role:
        logger.error("SystemRole.CUSTOMER is not configured in the database roles table.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Customer role is not properly configured in the system.",
        )

    # 1. Create and persist User record
    new_user = User(
        role_id=customer_role.id,
        email=clean_email,
        phone=clean_phone,
        full_name=full_name,
        hashed_password=hash_password(request.password),
        is_active=True,
        is_verified=True,
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(new_user)
    db.flush()  # Obtain new_user.id for customer record foreign key

    # 2. Link existing Customer record or create a new Customer profile
    existing_customer = db.execute(
        select(Customer).where(
            or_(
                func.lower(Customer.email) == clean_email,
                Customer.phone == clean_phone,
            )
        )
    ).scalars().first()

    if existing_customer:
        if existing_customer.user_id and existing_customer.user_id != new_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A customer profile with this contact is already linked to another user account.",
            )
        existing_customer.user_id = new_user.id
        if not existing_customer.email:
            existing_customer.email = clean_email
        if not existing_customer.full_name:
            existing_customer.full_name = full_name
        if request.address and request.address.strip():
            existing_customer.address = request.address.strip()
    else:
        new_customer = Customer(
            user_id=new_user.id,
            customer_type="RESIDENTIAL",
            full_name=full_name,
            email=clean_email,
            phone=clean_phone,
            address=request.address.strip() if request.address and request.address.strip() else "Residential Installation Site",
            city=request.city.strip() if request.city and request.city.strip() else "Local",
            state=request.state.strip() if request.state and request.state.strip() else "State",
            pincode=request.pincode.strip() if request.pincode and request.pincode.strip() else "000000",
            created_by=new_user.id,
            is_active=True,
        )
        db.add(new_customer)

    db.commit()

    # Load user with role and permissions for token response
    user_with_role = db.execute(
        select(User)
        .where(User.id == new_user.id)
        .options(
            selectinload(User.role).selectinload(Role.role_permissions).selectinload(RolePermission.permission)
        )
    ).scalar_one()

    # Issue JWT access token
    token_payload = {
        "sub": str(new_user.id),
        "email": new_user.email,
        "role": SystemRole.CUSTOMER,
    }
    access_token = create_access_token(data=token_payload)
    user_profile = build_user_profile(user_with_role)

    token_data = TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=user_profile,
    )

    logger.info(f"New customer registered successfully: user_id={new_user.id}, email={new_user.email}")

    return APIResponse(
        success=True,
        message="Customer account registered successfully.",
        data=token_data,
    )
