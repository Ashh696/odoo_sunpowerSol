import pytest
from fastapi.testclient import TestClient
from fastapi import Depends
from sqlalchemy import select
from app.main import app
from app.database import SessionLocal
from app.models.auth import User, Role
from app.utils.roles import SystemRole
from app.utils.security import hash_password, create_access_token
from app.dependencies import require_roles, require_permissions

client = TestClient(app)

# Register test routes on app for RBAC verification (do NOT name function starting with test_)
@app.get("/api/v1/test/super-admin-only")
def endpoint_super_admin_only(user: User = Depends(require_roles(SystemRole.SUPER_ADMIN))):
    return {"status": "ok", "role": user.role.slug}


@app.get("/api/v1/test/director-only")
def endpoint_director_only(user: User = Depends(require_roles(SystemRole.DIRECTOR))):
    return {"status": "ok", "role": user.role.slug}


@app.get("/api/v1/test/quotations-approve")
def endpoint_quotations_approve(user: User = Depends(require_permissions("quotations.approve"))):
    return {"status": "ok", "role": user.role.slug}


@pytest.fixture(scope="module")
def setup_test_users():
    db = SessionLocal()
    try:
        # Fetch roles
        sa_role = db.execute(select(Role).where(Role.slug == SystemRole.SUPER_ADMIN)).scalar_one()
        sales_role = db.execute(select(Role).where(Role.slug == SystemRole.SALES)).scalar_one()
        cust_role = db.execute(select(Role).where(Role.slug == SystemRole.CUSTOMER)).scalar_one()

        # 1. Active Super Admin
        admin_user = db.execute(select(User).where(User.email == "test_admin@sunpower.com")).scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                role_id=sa_role.id,
                email="test_admin@sunpower.com",
                full_name="Test Super Admin",
                hashed_password=hash_password("AdminPass123!"),
                is_active=True,
                is_verified=True,
            )
            db.add(admin_user)
        else:
            admin_user.hashed_password = hash_password("AdminPass123!")
            admin_user.is_active = True

        # 2. Inactive User
        inactive_user = db.execute(select(User).where(User.email == "test_inactive@sunpower.com")).scalar_one_or_none()
        if not inactive_user:
            inactive_user = User(
                role_id=sales_role.id,
                email="test_inactive@sunpower.com",
                full_name="Inactive Sales Rep",
                hashed_password=hash_password("InactivePass123!"),
                is_active=False,
                is_verified=True,
            )
            db.add(inactive_user)
        else:
            inactive_user.hashed_password = hash_password("InactivePass123!")
            inactive_user.is_active = False

        # 3. Active Sales User
        sales_user = db.execute(select(User).where(User.email == "test_sales@sunpower.com")).scalar_one_or_none()
        if not sales_user:
            sales_user = User(
                role_id=sales_role.id,
                email="test_sales@sunpower.com",
                full_name="Active Sales Rep",
                hashed_password=hash_password("SalesPass123!"),
                is_active=True,
                is_verified=True,
            )
            db.add(sales_user)
        else:
            sales_user.hashed_password = hash_password("SalesPass123!")
            sales_user.is_active = True

        # 4. Customer User
        cust_user = db.execute(select(User).where(User.email == "test_customer@sunpower.com")).scalar_one_or_none()
        if not cust_user:
            cust_user = User(
                role_id=cust_role.id,
                email="test_customer@sunpower.com",
                full_name="Rooftop Solar Customer",
                hashed_password=hash_password("CustomerPass123!"),
                is_active=True,
                is_verified=True,
            )
            db.add(cust_user)
        else:
            cust_user.hashed_password = hash_password("CustomerPass123!")
            cust_user.is_active = True

        db.commit()
        db.refresh(admin_user)
        db.refresh(inactive_user)
        db.refresh(sales_user)
        db.refresh(cust_user)

        return {
            "admin": admin_user,
            "inactive": inactive_user,
            "sales": sales_user,
            "customer": cust_user,
        }
    finally:
        db.close()


def test_login_successful(setup_test_users):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test_admin@sunpower.com", "password": "AdminPass123!"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    data = res["data"]
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test_admin@sunpower.com"
    assert data["user"]["role"]["slug"] == "SUPER_ADMIN"
    assert len(data["user"]["permissions"]) > 50


def test_login_incorrect_password(setup_test_users):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test_admin@sunpower.com", "password": "WrongPassword999"},
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_non_existent_email(setup_test_users):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@sunpower.com", "password": "AnyPassword123!"},
    )
    assert response.status_code == 401


def test_login_inactive_user_rejected(setup_test_users):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test_inactive@sunpower.com", "password": "InactivePass123!"},
    )
    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()


def test_get_current_user_profile(setup_test_users):
    # Login first
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "test_sales@sunpower.com", "password": "SalesPass123!"},
    ).json()
    token = login_res["data"]["access_token"]

    # Call /me with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    data = me_res.json()["data"]
    assert data["email"] == "test_sales@sunpower.com"
    assert data["role"]["slug"] == "SALES"
    assert "hashed_password" not in data
    assert "quotations.create" in data["permissions"]
    assert "users.manage" not in data["permissions"]  # Sales does not have user management


def test_missing_bearer_token_rejected():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "Missing authentication credentials" in response.json()["detail"]


def test_invalid_bearer_token_rejected():
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer this.token.is.completely.bogus"},
    )
    assert response.status_code == 401


def test_change_password(setup_test_users):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "test_customer@sunpower.com", "password": "CustomerPass123!"},
    ).json()
    token = login_res["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Incorrect current password
    fail_res = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": "WrongCurrentPassword", "new_password": "NewSecretPass2026!"},
    )
    assert fail_res.status_code == 400

    # Successful password change
    succ_res = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": "CustomerPass123!", "new_password": "NewSecretPass2026!"},
    )
    assert succ_res.status_code == 200

    # Old password no longer works
    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "test_customer@sunpower.com", "password": "CustomerPass123!"},
    )
    assert old_login.status_code == 401

    # New password works
    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "test_customer@sunpower.com", "password": "NewSecretPass2026!"},
    )
    assert new_login.status_code == 200


def test_rbac_role_authorization_and_rejection(setup_test_users):
    # Admin token
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "test_admin@sunpower.com", "password": "AdminPass123!"},
    ).json()
    admin_token = admin_login["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Sales token
    sales_login = client.post(
        "/api/v1/auth/login",
        json={"email": "test_sales@sunpower.com", "password": "SalesPass123!"},
    ).json()
    sales_token = sales_login["data"]["access_token"]
    sales_headers = {"Authorization": f"Bearer {sales_token}"}

    # 1. Super Admin route with Admin token -> OK
    res1 = client.get("/api/v1/test/super-admin-only", headers=admin_headers)
    assert res1.status_code == 200
    assert res1.json()["role"] == "SUPER_ADMIN"

    # 2. Super Admin route with Sales token -> 403 Forbidden
    res2 = client.get("/api/v1/test/super-admin-only", headers=sales_headers)
    assert res2.status_code == 403
    assert "Insufficient role privileges" in res2.json()["detail"]

    # 3. Director route with Admin token -> 403 Forbidden (Admin is not DIRECTOR)
    res3 = client.get("/api/v1/test/director-only", headers=admin_headers)
    assert res3.status_code == 403


def test_rbac_permission_authorization_and_rejection(setup_test_users):
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "test_admin@sunpower.com", "password": "AdminPass123!"},
    ).json()
    admin_headers = {"Authorization": f"Bearer {admin_login['data']['access_token']}"}

    sales_login = client.post(
        "/api/v1/auth/login",
        json={"email": "test_sales@sunpower.com", "password": "SalesPass123!"},
    ).json()
    sales_headers = {"Authorization": f"Bearer {sales_login['data']['access_token']}"}

    # Super Admin has all permissions wildcard -> OK
    res1 = client.get("/api/v1/test/quotations-approve", headers=admin_headers)
    assert res1.status_code == 200

    # Sales role does NOT have 'quotations.approve' -> 403 Forbidden
    res2 = client.get("/api/v1/test/quotations-approve", headers=sales_headers)
    assert res2.status_code == 403
    assert "quotations.approve" in res2.json()["detail"]


def test_customer_isolation_and_no_employee_link(setup_test_users):
    cust_login = client.post(
        "/api/v1/auth/login",
        json={"email": "test_customer@sunpower.com", "password": "NewSecretPass2026!"},
    ).json()
    cust_token = cust_login["data"]["access_token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # Customer trying to access Admin route -> 403 Forbidden
    res = client.get("/api/v1/test/super-admin-only", headers=cust_headers)
    assert res.status_code == 403

    # Verify customer account in database has no employee record
    db = SessionLocal()
    try:
        cust_user = db.execute(
            select(User).where(User.email == "test_customer@sunpower.com")
        ).scalar_one()
        assert cust_user.employee is None
        assert cust_user.role.slug == SystemRole.CUSTOMER
    finally:
        db.close()


def test_customer_self_registration_success():
    import uuid, random
    unique_suffix = uuid.uuid4().hex[:8]
    random_phone = f"+91{random.randint(1000000000, 9999999999)}"
    payload = {
        "full_name": "Rooftop Owner Test",
        "email": f"rooftop_{unique_suffix}@example.com",
        "phone": random_phone,
        "password": "SecurePassword123!",
        "address": "45 Green Energy Road, Solar Nagar",
        "city": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560001",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    res = response.json()
    assert res["success"] is True
    assert "access_token" in res["data"]
    assert res["data"]["user"]["role"]["slug"] == "CUSTOMER"
    assert res["data"]["user"]["email"] == payload["email"]

    # Verify user and customer link in database
    db = SessionLocal()
    try:
        from app.models.crm import Customer
        user = db.execute(select(User).where(User.email == payload["email"])).scalar_one()
        assert user.role.slug == "CUSTOMER"
        assert user.employee is None

        cust = db.execute(select(Customer).where(Customer.user_id == user.id)).scalar_one()
        assert cust.full_name == payload["full_name"]
        assert cust.phone == payload["phone"]
        assert cust.address == payload["address"]
    finally:
        db.close()


def test_customer_registration_duplicate_rejected():
    import uuid, random
    unique_suffix = uuid.uuid4().hex[:8]
    random_phone = f"+91{random.randint(1000000000, 9999999999)}"
    payload = {
        "full_name": "Duplicate Tester",
        "email": f"dup_{unique_suffix}@example.com",
        "phone": random_phone,
        "password": "SecurePassword123!",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()


def test_customer_registration_validation():
    # Short password
    res1 = client.post("/api/v1/auth/register", json={
        "full_name": "Short Pass",
        "email": "shortpass@example.com",
        "phone": "+919876543210",
        "password": "short",
    })
    assert res1.status_code in [400, 422]

    # Invalid / short phone
    res2 = client.post("/api/v1/auth/register", json={
        "full_name": "Short Phone",
        "email": "shortphone@example.com",
        "phone": "123",
        "password": "ValidPassword123!",
    })
    assert res2.status_code in [400, 422]

