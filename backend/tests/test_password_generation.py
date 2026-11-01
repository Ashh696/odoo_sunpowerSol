import re
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.database import SessionLocal
from app.utils.security import generate_human_friendly_password, verify_password, create_access_token
from app.models.auth import User, Employee, Department, Role
from app.utils.roles import SystemRole

client = TestClient(app)


def test_generate_human_friendly_password_format_and_entropy():
    """Verify password format, length, character diversity, and randomness."""
    passwords = [generate_human_friendly_password() for _ in range(50)]

    # All passwords must be unique
    assert len(set(passwords)) == 50

    # Pattern: CapitalizedWord + [@#$!%&] + 4digits + CapitalizedWord
    pattern = re.compile(r"^[A-Z][a-z]+[@#$!%&]\d{4}[A-Z][a-z]+$")

    for pwd in passwords:
        assert len(pwd) >= 8, f"Password {pwd} too short"
        assert pattern.match(pwd), f"Password {pwd} does not match expected human-friendly pattern"
        # Must contain at least one uppercase, one lowercase, one digit, one special char
        assert any(c.isupper() for c in pwd)
        assert any(c.islower() for c in pwd)
        assert any(c.isdigit() for c in pwd)
        assert any(c in "@#$!%&" for c in pwd)


def test_generate_password_endpoint_requires_auth():
    """GET /api/v1/employees/generate-password requires valid employee manage permissions."""
    resp = client.get("/api/v1/employees/generate-password")
    assert resp.status_code == 401


def test_generate_password_endpoint_success():
    """Super Admin can retrieve a freshly generated temporary password."""
    db = SessionLocal()
    try:
        sa_user = db.execute(
            select(User).join(Role).where(Role.slug == SystemRole.SUPER_ADMIN, User.is_active == True)
        ).scalars().first()
        assert sa_user is not None
        token = create_access_token({"sub": str(sa_user.id), "email": sa_user.email, "role": SystemRole.SUPER_ADMIN})
        headers = {"Authorization": f"Bearer {token}"}

        # Fetch generated password
        gen_resp = client.get("/api/v1/employees/generate-password", headers=headers)
        assert gen_resp.status_code == 200
        data = gen_resp.json()
        assert data["success"] is True
        generated_pwd = data["data"]["password"]
        assert len(generated_pwd) >= 8
        assert any(c.isupper() for c in generated_pwd)
        assert any(c.islower() for c in generated_pwd)
        assert any(c.isdigit() for c in generated_pwd)
        assert any(c in "@#$!%&" for c in generated_pwd)
    finally:
        db.close()


def test_create_employee_with_generated_password_and_login():
    """
    Super Admin provisions employee with generated password.
    Employee immediately logs in successfully with that password.
    """
    db = SessionLocal()
    try:
        # 1. Super Admin auth
        sa_user = db.execute(
            select(User).join(Role).where(Role.slug == SystemRole.SUPER_ADMIN, User.is_active == True)
        ).scalars().first()
        token = create_access_token({"sub": str(sa_user.id), "email": sa_user.email, "role": SystemRole.SUPER_ADMIN})
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get department
        dept = db.execute(select(Department)).scalars().first()
        assert dept is not None

        # 3. Generate human friendly password
        temp_password = generate_human_friendly_password()
        uid = uuid.uuid4().hex[:6]
        emp_code = f"TEST-GEN-{uid.upper()}"
        emp_email = f"emp.gen.{uid}@sunpowersolutions.com"

        payload = {
            "employee_code": emp_code,
            "department_id": dept.id,
            "designation": "Solar Technician",
            "employment_type": "FULL_TIME",
            "joining_date": "2026-11-01",
            "full_name": f"Test Technician {uid}",
            "email": emp_email,
            "role_slug": "FIELD_TECHNICIAN",
            "create_login_account": True,
            "password": temp_password,
        }

        create_resp = client.post("/api/v1/employees", json=payload, headers=headers)
        assert create_resp.status_code == 201, f"Create employee failed: {create_resp.text}"

        # 4. Verify user record has bcrypt hash and NOT plaintext password
        created_user = db.execute(select(User).where(User.email == emp_email)).scalar_one_or_none()
        assert created_user is not None
        assert created_user.hashed_password != temp_password
        assert created_user.hashed_password.startswith("$2b$")
        assert verify_password(temp_password, created_user.hashed_password)

        # 5. Verify the new employee can immediately log in with their generated password
        emp_login = client.post(
            "/api/v1/auth/login",
            json={"email": emp_email, "password": temp_password},
        )
        assert emp_login.status_code == 200, f"Employee login failed: {emp_login.text}"
        emp_token_data = emp_login.json()["data"]
        assert "access_token" in emp_token_data
        assert emp_token_data["user"]["role"]["slug"] == "FIELD_TECHNICIAN"
    finally:
        db.close()
