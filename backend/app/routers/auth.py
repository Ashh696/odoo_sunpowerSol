from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func
from datetime import datetime, timezone

from app.database import get_db
from app.models.auth import User, Role, RolePermission
from app.schemas import (
    APIResponse,
    LoginRequest,
    TokenResponse,
    UserProfileResponse,
    RoleInfo,
    ChangePasswordRequest,
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
