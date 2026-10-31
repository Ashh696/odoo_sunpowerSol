import os
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.auth import User, Role
from app.utils.roles import SystemRole
from app.utils.security import hash_password
from app.services.seed import seed_reference_data
import logging

logger = logging.getLogger(__name__)


def bootstrap_super_admin(
    db: Session,
    email: str,
    password: str,
    full_name: str = "System Super Administrator",
    phone: Optional[str] = None,
) -> Tuple[User, bool]:
    """
    Idempotently bootstrap the initial Super Admin account.
    Returns (User, was_created: bool).
    """
    if not email or not password:
        raise ValueError("Super Admin email and password must be provided.")

    if len(password) < 8:
        raise ValueError("Super Admin password must be at least 8 characters long.")

    # Ensure reference data is seeded first
    seed_reference_data(db)

    # Fetch SUPER_ADMIN role
    admin_role = db.execute(
        select(Role).where(Role.slug == SystemRole.SUPER_ADMIN)
    ).scalar_one()

    # Check if a user with this email or an existing SUPER_ADMIN already exists
    existing_user = db.execute(
        select(User).where(User.email == email.lower().strip())
    ).scalar_one_or_none()

    if existing_user:
        logger.info(f"User with email '{email}' already exists. Skipping bootstrap.")
        return existing_user, False

    # Check if ANY super admin user already exists
    existing_admin = db.execute(
        select(User).where(User.role_id == admin_role.id)
    ).first()

    if existing_admin:
        logger.warning(
            f"A Super Admin account already exists in the system. "
            f"Refusing to create duplicate Super Admin via bootstrap."
        )
        return existing_admin[0], False

    # Create new Super Admin user
    new_admin = User(
        role_id=admin_role.id,
        email=email.lower().strip(),
        phone=phone.strip() if phone else None,
        full_name=full_name.strip(),
        hashed_password=hash_password(password),
        is_active=True,
        is_verified=True,
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    logger.info(f"Successfully bootstrapped Super Admin account: {new_admin.email}")
    return new_admin, True
