import pytest
import uuid
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.database import SessionLocal
from app.models.auth import User, Role
from app.models.crm import Product
from app.models.workflow import AuditLog
from app.utils.security import hash_password, create_access_token
from app.utils.roles import SystemRole

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_product_auth():
    """
    Set up authenticated test users and JWT bearer tokens across canonical roles:
    - SUPER_ADMIN
    - TECHNICAL_MANAGER
    - WAREHOUSE_PROCUREMENT
    - SALES
    - FIELD_TECHNICIAN
    - CUSTOMER
    """
    tokens = {}
    user_ids = {}

    with SessionLocal() as db:
        roles = {
            SystemRole.SUPER_ADMIN: db.execute(select(Role).where(Role.slug == SystemRole.SUPER_ADMIN)).scalar_one(),
            SystemRole.TECHNICAL_MANAGER: db.execute(select(Role).where(Role.slug == SystemRole.TECHNICAL_MANAGER)).scalar_one(),
            SystemRole.WAREHOUSE_PROCUREMENT: db.execute(select(Role).where(Role.slug == SystemRole.WAREHOUSE_PROCUREMENT)).scalar_one(),
            SystemRole.SALES: db.execute(select(Role).where(Role.slug == SystemRole.SALES)).scalar_one(),
            SystemRole.FIELD_TECHNICIAN: db.execute(select(Role).where(Role.slug == SystemRole.FIELD_TECHNICIAN)).scalar_one(),
            SystemRole.CUSTOMER: db.execute(select(Role).where(Role.slug == SystemRole.CUSTOMER)).scalar_one(),
        }

        for role_slug, role_obj in roles.items():
            email = f"test_{role_slug.lower()}_prod@sunpower.com"
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if not user:
                user = User(
                    role_id=role_obj.id,
                    email=email,
                    full_name=f"Test {role_slug}",
                    hashed_password=hash_password("Pass123!Safe"),
                    is_active=True,
                    is_verified=True,
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            token = create_access_token(
                data={
                    "sub": str(user.id),
                    "role": role_obj.slug,
                    "email": user.email,
                }
            )
            tokens[role_slug] = token
            user_ids[role_slug] = user.id

    return tokens, user_ids


def test_product_creation_and_retrieval(setup_product_auth):
    tokens, user_ids = setup_product_auth
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}

    unique_code = f"MOD-550W-{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "product_code": unique_code,
        "name": "550W Mono PERC Half-Cut Solar Module",
        "category": "SOLAR_PANEL",
        "brand": "SunPower Tier-1",
        "model_number": "SP-550-MH",
        "wattage_or_capacity": "550W",
        "unit_of_measure": "NOS",
        "is_serialized": True,
        "base_price": 9500.00,
        "tax_rate_percent": 12.00,
        "min_stock_alert": 20.00,
        "is_active": True,
    }

    # 1. Create product
    res = client.post("/api/v1/products", json=payload, headers=admin_headers)
    assert res.status_code == 201, f"Failed to create product: {res.text}"
    data = res.json()["data"]
    assert data["product_code"] == unique_code
    assert data["name"] == payload["name"]
    assert data["category"] == "SOLAR_PANEL"
    assert data["base_price"] == 9500.00
    assert data["is_serialized"] is True
    prod_id = data["id"]

    # 2. Retrieve product by ID
    get_res = client.get(f"/api/v1/products/{prod_id}", headers=admin_headers)
    assert get_res.status_code == 200
    get_data = get_res.json()["data"]
    assert get_data["id"] == prod_id
    assert get_data["product_code"] == unique_code
    assert get_data["brand"] == "SunPower Tier-1"


def test_product_search_filtering_and_pagination(setup_product_auth):
    tokens, _ = setup_product_auth
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}

    tag = uuid.uuid4().hex[:5].upper()
    p1 = {
        "product_code": f"INV-5KW-{tag}",
        "name": f"5kW Hybrid Solar Inverter {tag}",
        "category": "INVERTER",
        "brand": "Solis Power",
        "model_number": "SOL-5K-HYB",
        "wattage_or_capacity": "5kW",
        "unit_of_measure": "NOS",
        "is_serialized": True,
        "base_price": 54000.00,
        "tax_rate_percent": 18.00,
        "min_stock_alert": 5.00,
        "is_active": True,
    }
    p2 = {
        "product_code": f"BAT-150AH-{tag}",
        "name": f"150Ah Lithium Iron Phosphate Battery {tag}",
        "category": "BATTERY",
        "brand": "Exide Life",
        "model_number": "EX-150-LFP",
        "wattage_or_capacity": "150Ah",
        "unit_of_measure": "NOS",
        "is_serialized": True,
        "base_price": 38000.00,
        "tax_rate_percent": 18.00,
        "min_stock_alert": 3.00,
        "is_active": True,
    }
    p3 = {
        "product_code": f"STR-ELEV-{tag}",
        "name": f"Elevated HDG Mounting Structure {tag}",
        "category": "STRUCTURE",
        "brand": "SolarMount",
        "model_number": "SM-ELEV-4M",
        "wattage_or_capacity": "4kW",
        "unit_of_measure": "SETS",
        "is_serialized": False,
        "base_price": 12000.00,
        "tax_rate_percent": 18.00,
        "min_stock_alert": 10.00,
        "is_active": False,
    }

    for p in (p1, p2, p3):
        r = client.post("/api/v1/products", json=p, headers=admin_headers)
        assert r.status_code == 201

    # Filter by category
    cat_res = client.get(f"/api/v1/products?category=INVERTER&search={tag}", headers=admin_headers)
    assert cat_res.status_code == 200
    cat_items = cat_res.json()["data"]["items"]
    assert any(item["product_code"] == p1["product_code"] for item in cat_items)
    assert not any(item["product_code"] == p2["product_code"] for item in cat_items)

    # Search by brand
    search_res = client.get(f"/api/v1/products?search=Exide", headers=admin_headers)
    assert search_res.status_code == 200
    search_items = search_res.json()["data"]["items"]
    assert any(item["brand"] == "Exide Life" for item in search_items)

    # Filter by active status
    active_res = client.get(f"/api/v1/products?is_active=false&search={tag}", headers=admin_headers)
    assert active_res.status_code == 200
    inactive_items = active_res.json()["data"]["items"]
    assert len(inactive_items) == 1
    assert inactive_items[0]["product_code"] == p3["product_code"]

    # Pagination
    page_res = client.get(f"/api/v1/products?search={tag}&limit=2&page=1", headers=admin_headers)
    assert page_res.status_code == 200
    page_data = page_res.json()["data"]
    assert page_data["limit"] == 2
    assert len(page_data["items"]) <= 2
    assert page_data["total"] == 3
    assert page_data["total_pages"] == 2


def test_duplicate_product_code_rejection(setup_product_auth):
    tokens, _ = setup_product_auth
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}

    dup_code = f"DUP-CODE-{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "product_code": dup_code,
        "name": "Standard DC Cable 4 sqmm Red",
        "category": "CABLES",
        "brand": "Polycab Solar",
        "unit_of_measure": "METERS",
        "base_price": 45.00,
        "tax_rate_percent": 18.00,
        "min_stock_alert": 500.00,
        "is_active": True,
    }

    res1 = client.post("/api/v1/products", json=payload, headers=admin_headers)
    assert res1.status_code == 201

    # Attempt same code (with lower-case variant)
    payload_dup = dict(payload)
    payload_dup["product_code"] = dup_code.lower()
    res2 = client.post("/api/v1/products", json=payload_dup, headers=admin_headers)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_invalid_numeric_values_rejection(setup_product_auth):
    tokens, _ = setup_product_auth
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}

    # 1. Negative price
    bad_price = {
        "product_code": f"ERR-1-{uuid.uuid4().hex[:4]}",
        "name": "Invalid Price Product",
        "category": "MISC",
        "base_price": -50.00,
        "tax_rate_percent": 12.00,
        "min_stock_alert": 5.00,
    }
    r1 = client.post("/api/v1/products", json=bad_price, headers=admin_headers)
    assert r1.status_code == 422

    # 2. Negative tax rate
    bad_tax = {
        "product_code": f"ERR-2-{uuid.uuid4().hex[:4]}",
        "name": "Invalid Tax Product",
        "category": "MISC",
        "base_price": 100.00,
        "tax_rate_percent": -5.00,
        "min_stock_alert": 5.00,
    }
    r2 = client.post("/api/v1/products", json=bad_tax, headers=admin_headers)
    assert r2.status_code == 422

    # 3. Tax rate exceeding 100%
    bad_tax2 = {
        "product_code": f"ERR-3-{uuid.uuid4().hex[:4]}",
        "name": "Excessive Tax Product",
        "category": "MISC",
        "base_price": 100.00,
        "tax_rate_percent": 150.00,
        "min_stock_alert": 5.00,
    }
    r3 = client.post("/api/v1/products", json=bad_tax2, headers=admin_headers)
    assert r3.status_code == 422

    # 4. Blank name
    bad_name = {
        "product_code": f"ERR-4-{uuid.uuid4().hex[:4]}",
        "name": "   ",
        "category": "MISC",
        "base_price": 100.00,
        "tax_rate_percent": 12.00,
        "min_stock_alert": 5.00,
    }
    r4 = client.post("/api/v1/products", json=bad_name, headers=admin_headers)
    assert r4.status_code == 422


def test_product_authorization_and_permissions(setup_product_auth):
    tokens, _ = setup_product_auth

    sample_product = {
        "product_code": f"AUTH-TEST-{uuid.uuid4().hex[:6].upper()}",
        "name": "Earthing Copper Rod 2m",
        "category": "EARTHING",
        "brand": "SafeEarth",
        "base_price": 1800.00,
        "tax_rate_percent": 18.00,
        "min_stock_alert": 15.00,
        "is_active": True,
    }

    # 1. Anonymous request (no token) -> 401 Unauthorized
    anon_res = client.get("/api/v1/products")
    assert anon_res.status_code == 401

    # 2. CUSTOMER cannot access or read product catalog -> 403 Forbidden
    cust_headers = {"Authorization": f"Bearer {tokens[SystemRole.CUSTOMER]}"}
    cust_get = client.get("/api/v1/products", headers=cust_headers)
    assert cust_get.status_code == 403

    cust_create = client.post("/api/v1/products", json=sample_product, headers=cust_headers)
    assert cust_create.status_code == 403

    # 3. FIELD_TECHNICIAN cannot create or update products -> 403 Forbidden
    tech_headers = {"Authorization": f"Bearer {tokens[SystemRole.FIELD_TECHNICIAN]}"}
    tech_create = client.post("/api/v1/products", json=sample_product, headers=tech_headers)
    assert tech_create.status_code == 403

    # 4. SALES can read products (needed for quote preparation), but cannot create
    sales_headers = {"Authorization": f"Bearer {tokens[SystemRole.SALES]}"}
    sales_get = client.get("/api/v1/products", headers=sales_headers)
    assert sales_get.status_code == 200

    sales_create = client.post("/api/v1/products", json=sample_product, headers=sales_headers)
    assert sales_create.status_code == 403

    # 5. TECHNICAL_MANAGER and WAREHOUSE_PROCUREMENT have manage rights
    tm_headers = {"Authorization": f"Bearer {tokens[SystemRole.TECHNICAL_MANAGER]}"}
    tm_create = client.post("/api/v1/products", json=sample_product, headers=tm_headers)
    assert tm_create.status_code == 201


def test_product_update_and_activation_lifecycle(setup_product_auth):
    tokens, _ = setup_product_auth
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}

    init_code = f"CYCLE-{uuid.uuid4().hex[:6].upper()}"
    p_init = {
        "product_code": init_code,
        "name": "3kW Grid-Tie Inverter Initial",
        "category": "INVERTER",
        "brand": "OldBrand",
        "base_price": 28000.00,
        "tax_rate_percent": 18.00,
        "min_stock_alert": 5.00,
        "is_active": True,
    }
    c_res = client.post("/api/v1/products", json=p_init, headers=admin_headers)
    assert c_res.status_code == 201
    prod_id = c_res.json()["data"]["id"]

    # 1. Update price, brand, and specifications
    update_payload = {
        "name": "3kW Grid-Tie Inverter Advanced V2",
        "brand": "Growatt Premium",
        "base_price": 31500.00,
        "wattage_or_capacity": "3kW",
    }
    u_res = client.put(f"/api/v1/products/{prod_id}", json=update_payload, headers=admin_headers)
    assert u_res.status_code == 200
    u_data = u_res.json()["data"]
    assert u_data["name"] == "3kW Grid-Tie Inverter Advanced V2"
    assert u_data["brand"] == "Growatt Premium"
    assert u_data["base_price"] == 31500.00
    assert u_data["wattage_or_capacity"] == "3kW"

    # 2. Deactivate product via PATCH status
    deact_res = client.patch(
        f"/api/v1/products/{prod_id}/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert deact_res.status_code == 200
    assert deact_res.json()["data"]["is_active"] is False

    # Verify inactive via GET
    chk_res = client.get(f"/api/v1/products/{prod_id}", headers=admin_headers)
    assert chk_res.status_code == 200
    assert chk_res.json()["data"]["is_active"] is False

    # 3. Reactivate product via PATCH status
    act_res = client.patch(
        f"/api/v1/products/{prod_id}/status",
        json={"is_active": True},
        headers=admin_headers,
    )
    assert act_res.status_code == 200
    assert act_res.json()["data"]["is_active"] is True


def test_product_audit_logging(setup_product_auth):
    tokens, user_ids = setup_product_auth
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}
    admin_id = user_ids[SystemRole.SUPER_ADMIN]

    audit_code = f"AUDIT-PRD-{uuid.uuid4().hex[:6].upper()}"
    p = {
        "product_code": audit_code,
        "name": "Audit Logging Test Light Arrester",
        "category": "LIGHTNING_ARRESTER",
        "base_price": 2500.00,
        "tax_rate_percent": 18.00,
        "min_stock_alert": 5.00,
        "is_active": True,
    }

    # 1. Create
    c_res = client.post("/api/v1/products", json=p, headers=admin_headers)
    assert c_res.status_code == 201
    prod_id = c_res.json()["data"]["id"]

    # 2. Update
    u_res = client.put(f"/api/v1/products/{prod_id}", json={"base_price": 2700.00}, headers=admin_headers)
    assert u_res.status_code == 200

    # 3. Deactivate
    d_res = client.patch(f"/api/v1/products/{prod_id}/status", json={"is_active": False}, headers=admin_headers)
    assert d_res.status_code == 200

    # Verify AuditLog entries in database
    with SessionLocal() as db:
        logs = db.execute(
            select(AuditLog)
            .where(AuditLog.entity_name == "PRODUCT", AuditLog.entity_id == prod_id)
            .order_by(AuditLog.created_at.asc())
        ).scalars().all()

        actions = [log.action for log in logs]
        assert "CREATE" in actions
        assert "UPDATE" in actions
        assert "DEACTIVATE" in actions

        create_log = next(log for log in logs if log.action == "CREATE")
        assert create_log.user_id == admin_id
        assert create_log.details.get("product_code") == audit_code
