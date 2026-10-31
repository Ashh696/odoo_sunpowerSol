from typing import List, Callable, Set, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app.database import get_db
from app.models.auth import User, Role, RolePermission, Permission
from app.utils.security import decode_access_token, TokenExpiredError, TokenInvalidError
from app.utils.roles import SystemRole
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer token extractor
http_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts Bearer JWT from Authorization header, validates signature & expiry,
    and loads active User with Role and RolePermissions from database.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except TokenExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except TokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing subject identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user with role and permissions eager-loaded
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.role).selectinload(Role.role_permissions).selectinload(RolePermission.permission)
        )
    )
    user = db.execute(stmt).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive. Please contact system administrator.",
        )

    return user


def get_user_permissions(user: User) -> Set[str]:
    """
    Extract set of permission codes associated with user's role.
    If role is SUPER_ADMIN, returns all system permissions or wildcard.
    """
    if not user or not user.role:
        return set()

    permissions = set()
    for rp in user.role.role_permissions:
        if rp.permission and rp.permission.code:
            permissions.add(rp.permission.code)

    return permissions


def require_roles(*allowed_roles: str) -> Callable:
    """
    Dependency factory to restrict endpoint access to specific canonical roles.
    Example: Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.DIRECTOR))
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.role or current_user.role.slug not in allowed_roles:
            logger.warning(
                f"Unauthorized role access attempt: user_id={current_user.id}, "
                f"role={current_user.role.slug if current_user.role else 'None'}, "
                f"required={allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role privileges to access this resource",
            )
        return current_user

    return role_checker


def require_permissions(*required_permissions: str) -> Callable:
    """
    Dependency factory to restrict endpoint access to users possessing all specified permissions.
    SUPER_ADMIN bypasses granular permission restrictions.
    Example: Depends(require_permissions('quotations.approve'))
    """
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        # SUPER_ADMIN has full system privileges
        if current_user.role and current_user.role.slug == SystemRole.SUPER_ADMIN:
            return current_user

        user_perms = get_user_permissions(current_user)
        missing_perms = [p for p in required_permissions if p not in user_perms]

        if missing_perms:
            logger.warning(
                f"Missing permissions: user_id={current_user.id}, "
                f"role={current_user.role.slug if current_user.role else 'None'}, "
                f"missing={missing_perms}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {', '.join(missing_perms)}",
            )
        return current_user

    return permission_checker
