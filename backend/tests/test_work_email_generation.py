import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.database import SessionLocal
from app.utils.security import (
    generate_human_friendly_password,
    normalize_name_for_email,
    generate_unique_work_email,
    create_access_token,
)
from app.models.auth import User, Employee, Department, Role
from app.utils.roles import SystemRole

client = TestClient(app)


def test_normalize_name_for_email():
    """Verify name normalization strips diacritics, symbols, spaces, and lowercases."""
    assert normalize_name_for_email("Ramesh") == "ramesh"
    assert normalize_name_for_email("Kumar") == "kumar"
    assert normalize_name_for_email("Mary-Jane") == "maryjane"
    assert normalize_name_for_email("O'Connor") == "oconnor"
    assert normalize_name_for_email("Renée") == "renee"
    assert normalize_name_for_email("  Al-Rashid  ") == "alrashid"
    assert normalize_name_for_email("") == ""


def test_generate_unique_work_email_duplicate_suffixing():
    """Verify duplicate names automatically resolve with sequential suffixes."""
    db = SessionLocal()
    try:
        uid = uuid.uuid4().hex[:6]
        first_name = f"Test{uid}"
        last_name = "Duplicate"

        # 1st: base email firstname.lastname@sunpower.com
        email1 = generate_unique_work_email(db, first_name, last_name)
        assert email1 == f"test{uid}.duplicate@sunpower.com"

        # Simulate existing user in DB with email1
        role = db.execute(select(Role).where(Role.slug == SystemRole.FIELD_TECHNICIAN)).scalar_one()
        user1 = User(
            role_id=role.id,
            email=email1,
            full_name=f"{first_name} {last_name}",
            hashed_password="hashed_dummy_password",
            is_active=True,
        )
        db.add(user1)
        db.commit()

        # 2nd: duplicate suffix firstname.lastname2@sunpower.com
        email2 = generate_unique_work_email(db, first_name, last_name)
        assert email2 == f"test{uid}.duplicate2@sunpower.com"

        # Simulate user2 in DB
        user2 = User(
            role_id=role.id,
            email=email2,
            full_name=f"{first_name} {last_name} 2",
            hashed_password="hashed_dummy_password",
            is_active=True,
        )
        db.add(user2)
        db.commit()

        # 3rd: duplicate suffix firstname.lastname3@sunpower.com
        email3 = generate_unique_work_email(db, first_name, last_name)
        assert email3 == f"test{uid}.duplicate3@sunpower.com"

        # Cleanup
        db.delete(user1)
        db.delete(user2)
        db.commit()
    finally:
        db.close()


def test_generate_email_api_endpoint():
    """GET /api/v1/employees/generate-email returns unique email and company domain."""
    db = SessionLocal()
    try:
        sa_user = db.execute(
            select(User).join(Role).where(Role.slug == SystemRole.SUPER_ADMIN, User.is_active == True)
        ).scalars().first()
        token = create_access_token({"sub": str(sa_user.id), "email": sa_user.email, "role": SystemRole.SUPER_ADMIN})
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get(
            "/api/v1/employees/generate-email",
            params={"first_name": "Suresh", "last_name": "Patel"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "@sunpower.com" in data["data"]["email"]
        assert data["data"]["domain"] == "sunpower.com"
        assert data["data"]["is_mailbox_provisioned"] is False
    finally:
        db.close()


def test_create_employee_auto_generated_email_and_login():
    """
    Super Admin creates an employee with first_name and last_name (no email provided).
    Backend automatically generates the work email, hashes password, and employee logs in.
    """
    db = SessionLocal()
    try:
        # Super Admin auth
        sa_user = db.execute(
            select(User).join(Role).where(Role.slug == SystemRole.SUPER_ADMIN, User.is_active == True)
        ).scalars().first()
        token = create_access_token({"sub": str(sa_user.id), "email": sa_user.email, "role": SystemRole.SUPER_ADMIN})
        headers = {"Authorization": f"Bearer {token}"}

        dept = db.execute(select(Department)).scalars().first()
        assert dept is not None

        uid = uuid.uuid4().hex[:6]
        fn = f"Dev{uid}"
        ln = "Solar"
        temp_pw = generate_human_friendly_password()

        # 1. Create first employee with auto-generated email
        payload1 = {
            "employee_code": f"EMP-AUTO1-{uid.upper()}",
            "department_id": dept.id,
            "designation": "Solar Engineer",
            "employment_type": "FULL_TIME",
            "joining_date": "2026-11-01",
            "first_name": fn,
            "last_name": ln,
            # Notice: email is omitted so system generates it
            "role_slug": "TECHNICAL_MANAGER",
            "create_login_account": True,
            "password": temp_pw,
        }

        resp1 = client.post("/api/v1/employees", json=payload1, headers=headers)
        assert resp1.status_code == 201, f"Failed create 1: {resp1.text}"
        emp1_data = resp1.json()["data"]
        expected_email1 = f"dev{uid}.solar@sunpower.com"
        assert emp1_data["email"] == expected_email1

        # 2. Verify new employee can log in with generated email and temporary password
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": expected_email1, "password": temp_pw},
        )
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        assert login_res.json()["data"]["user"]["email"] == expected_email1

        # 3. Create second employee with same name -> automatically resolves duplicate to suffix 2
        payload2 = {
            "employee_code": f"EMP-AUTO2-{uid.upper()}",
            "department_id": dept.id,
            "designation": "Senior Engineer",
            "employment_type": "FULL_TIME",
            "joining_date": "2026-11-01",
            "first_name": fn,
            "last_name": ln,
            "role_slug": "FIELD_TECHNICIAN",
            "create_login_account": True,
            "password": temp_pw,
        }

        resp2 = client.post("/api/v1/employees", json=payload2, headers=headers)
        assert resp2.status_code == 201, f"Failed create 2: {resp2.text}"
        emp2_data = resp2.json()["data"]
        expected_email2 = f"dev{uid}.solar2@sunpower.com"
        assert emp2_data["email"] == expected_email2

        # 4. Verify second employee can log in with their suffixed work email
        login_res2 = client.post(
            "/api/v1/auth/login",
            json={"email": expected_email2, "password": temp_pw},
        )
        assert login_res2.status_code == 200, f"Login 2 failed: {login_res2.text}"
        assert login_res2.json()["data"]["user"]["email"] == expected_email2
    finally:
        db.close()


def test_customer_registration_remains_unchanged():
    """Verify customer self-registration accepts personal email domains (e.g. gmail.com)."""
    uid = uuid.uuid4().hex[:6]
    cust_email = f"customer.{uid}@gmail.com"
    payload = {
        "full_name": f"Customer {uid}",
        "email": cust_email,
        "phone": f"+9198{uuid.uuid4().int % 100000000:08d}",
        "password": "CustomerSecurePass2026!",
        "address": "123 Green Way, Bangalore",
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["data"]["user"]["email"] == cust_email
    assert data["data"]["user"]["role"]["slug"] == "CUSTOMER"
