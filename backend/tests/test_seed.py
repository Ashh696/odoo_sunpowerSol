import pytest
from sqlalchemy import select
from app.database import SessionLocal
from app.models.auth import Role, Permission, RolePermission, User
from app.utils.roles import SystemRole
from app.services.seed import seed_reference_data, DEFINED_PERMISSIONS, ROLE_PERMISSION_MATRIX


def test_seed_creates_exactly_nine_canonical_roles():
    db = SessionLocal()
    try:
        # Run seed
        seed_reference_data(db)

        # Query all system roles
        roles = db.execute(select(Role)).scalars().all()
        role_slugs = {r.slug for r in roles}

        assert len(role_slugs) == 9
        assert role_slugs == set(SystemRole.ALL_ROLES)

        for role in roles:
            assert role.is_system_role is True
            assert role.name is not None
            assert len(role.name) > 0
    finally:
        db.close()


def test_seed_creates_all_permissions_and_mappings():
    db = SessionLocal()
    try:
        # Check permissions
        perms = db.execute(select(Permission)).scalars().all()
        perm_codes = {p.code for p in perms}

        expected_codes = {p[0] for p in DEFINED_PERMISSIONS}
        assert perm_codes == expected_codes
        assert len(perms) == len(DEFINED_PERMISSIONS)

        # Check role permission allocations
        super_admin_role = db.execute(
            select(Role).where(Role.slug == SystemRole.SUPER_ADMIN)
        ).scalar_one()

        sa_mappings = db.execute(
            select(RolePermission).where(RolePermission.role_id == super_admin_role.id)
        ).scalars().all()

        # Super admin should have all permissions
        assert len(sa_mappings) == len(DEFINED_PERMISSIONS)

        # Customer role should only have customer-specific permissions
        customer_role = db.execute(
            select(Role).where(Role.slug == SystemRole.CUSTOMER)
        ).scalar_one()

        cust_mappings = db.execute(
            select(RolePermission).where(RolePermission.role_id == customer_role.id)
        ).scalars().all()

        assert len(cust_mappings) == len(ROLE_PERMISSION_MATRIX[SystemRole.CUSTOMER])
        assert len(cust_mappings) < len(DEFINED_PERMISSIONS)
    finally:
        db.close()


def test_seed_idempotency_does_not_duplicate():
    db = SessionLocal()
    try:
        # Record initial counts
        initial_roles_count = len(db.execute(select(Role)).scalars().all())
        initial_perms_count = len(db.execute(select(Permission)).scalars().all())
        initial_mappings_count = len(db.execute(select(RolePermission)).scalars().all())

        # Re-run seed
        res = seed_reference_data(db)

        # Result should indicate 0 created
        assert res["roles_created"] == 0
        assert res["permissions_created"] == 0
        assert res["mappings_created"] == 0

        # Counts must remain identical
        after_roles_count = len(db.execute(select(Role)).scalars().all())
        after_perms_count = len(db.execute(select(Permission)).scalars().all())
        after_mappings_count = len(db.execute(select(RolePermission)).scalars().all())

        assert after_roles_count == initial_roles_count
        assert after_perms_count == initial_perms_count
        assert after_mappings_count == initial_mappings_count
    finally:
        db.close()
