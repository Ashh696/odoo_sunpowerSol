import pytest
import uuid
from decimal import Decimal
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.database import SessionLocal
from app.models.auth import User, Role
from app.models.crm import Customer, Enquiry, Quotation, Product
from app.models.projects import Order, Project, BomTemplate, BomItem, ProjectBomItem
from app.models.workflow import AuditLog
from app.utils.security import hash_password, create_access_token
from app.utils.roles import SystemRole

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_bom_auth_and_data():
    """
    Set up authenticated test users, JWT tokens, test products, and a test project.
    Roles tested:
    - SUPER_ADMIN (manage)
    - TECHNICAL_MANAGER (manage)
    - DIRECTOR (read-only)
    - WAREHOUSE_PROCUREMENT (read-only)
    - SALES (blocked)
    - FIELD_TECHNICIAN (blocked)
    - CUSTOMER (blocked)
    """
    tokens = {}
    user_ids = {}
    products = {}

    with SessionLocal() as db:
        role_slugs = [
            SystemRole.SUPER_ADMIN,
            SystemRole.TECHNICAL_MANAGER,
            SystemRole.DIRECTOR,
            SystemRole.WAREHOUSE_PROCUREMENT,
            SystemRole.SALES,
            SystemRole.FIELD_TECHNICIAN,
            SystemRole.CUSTOMER,
        ]

        for slug in role_slugs:
            role_obj = db.execute(select(Role).where(Role.slug == slug)).scalar_one()
            email = f"test_{slug.lower()}_bom@sunpower.com"
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if not user:
                user = User(
                    role_id=role_obj.id,
                    email=email,
                    full_name=f"Test {slug} BOM",
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
            tokens[slug] = token
            user_ids[slug] = user.id

        admin_id = user_ids[SystemRole.SUPER_ADMIN]

        # Create active test products
        suffix = uuid.uuid4().hex[:6].upper()
        p_panel = Product(
            product_code=f"PANEL-{suffix}",
            name="540W Mono PERC Panel",
            category="SOLAR_PANEL",
            brand="SunPower",
            model_number="SP-540W",
            unit_of_measure="NOS",
            base_price=Decimal("8500.00"),
            tax_rate_percent=Decimal("12.00"),
            min_stock_alert=Decimal("10.00"),
            is_active=True,
        )
        p_inverter = Product(
            product_code=f"INV-{suffix}",
            name="3kW Grid Tie Inverter",
            category="INVERTER",
            brand="Growatt",
            model_number="MIN-3000TL",
            unit_of_measure="NOS",
            base_price=Decimal("32000.00"),
            tax_rate_percent=Decimal("12.00"),
            min_stock_alert=Decimal("5.00"),
            is_active=True,
        )
        p_cable = Product(
            product_code=f"CAB-{suffix}",
            name="4 sq mm Solar DC Cable",
            category="CABLES_WIRES",
            brand="Polycab",
            model_number="DC-4SQMM",
            unit_of_measure="MTR",
            base_price=Decimal("45.00"),
            tax_rate_percent=Decimal("18.00"),
            min_stock_alert=Decimal("100.00"),
            is_active=True,
        )
        p_inactive = Product(
            product_code=f"DISC-{suffix}",
            name="Discontinued Panel Mount",
            category="MOUNTING_STRUCTURE",
            brand="Generic",
            model_number="MNT-OLD",
            unit_of_measure="SET",
            base_price=Decimal("1200.00"),
            tax_rate_percent=Decimal("18.00"),
            min_stock_alert=Decimal("0.00"),
            is_active=False,
        )

        db.add_all([p_panel, p_inverter, p_cable, p_inactive])
        db.commit()
        db.refresh(p_panel)
        db.refresh(p_inverter)
        db.refresh(p_cable)
        db.refresh(p_inactive)

        products["panel"] = p_panel
        products["inverter"] = p_inverter
        products["cable"] = p_cable
        products["inactive"] = p_inactive

        # Create a test Project for Project BOM generation
        cust = Customer(
            customer_type="RESIDENTIAL",
            full_name=f"BOM Test Customer {suffix}",
            phone=f"97{uuid.uuid4().int % 100000000:08d}",
            email=f"bom_project_cust_{suffix.lower()}@test.com",
            address="456 Solar Avenue",
            city="Pune",
            state="Maharashtra",
            pincode="411001",
            created_by=admin_id,
        )
        db.add(cust)
        db.flush()

        enq = Enquiry(
            customer_id=cust.id,
            enquiry_number=f"ENQ-BOM-{suffix}",
            source="DIRECT",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("3.00"),
            status="QUOTED",
        )
        db.add(enq)
        db.flush()

        today = date.today()
        quot = Quotation(
            enquiry_id=enq.id,
            quotation_number=f"QUO-BOM-{suffix}",
            version=1,
            system_type="ON_GRID",
            capacity_kw=Decimal("3.00"),
            gross_amount=Decimal("165000.00"),
            net_payable_amount=Decimal("165000.00"),
            valid_until=today + timedelta(days=30),
            quotation_date=today,
            created_by=admin_id,
        )
        db.add(quot)
        db.flush()

        order = Order(
            order_number=f"ORD-BOM-{suffix}",
            quotation_id=quot.id,
            customer_id=cust.id,
            order_date=today,
            total_amount=Decimal("165000.00"),
            balance_amount=Decimal("165000.00"),
            created_by=admin_id,
        )
        db.add(order)
        db.flush()

        project = Project(
            project_code=f"PRJ-BOM-{suffix}",
            order_id=order.id,
            customer_id=cust.id,
            system_capacity_kw=Decimal("3.00"),
            system_type="ON_GRID",
            site_address="456 Solar Avenue, Pune",
            planned_start_date=today,
            planned_completion_date=today + timedelta(days=30),
            status="INITIATED",
        )
        db.add(project)
        db.commit()
        db.refresh(project)

    return tokens, user_ids, products, project.id


# ============================================================
# 1. BOM TEMPLATE CRUD & VALIDATION
# ============================================================

def test_bom_template_crud_and_validation(setup_bom_auth_and_data):
    tokens, user_ids, products, _ = setup_bom_auth_and_data
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}
    panel = products["panel"]
    inverter = products["inverter"]
    cable = products["cable"]
    inactive_p = products["inactive"]

    t_name = f"Residential 3kW Standard - {uuid.uuid4().hex[:6].upper()}"

    # 1. Successful creation with valid items
    payload = {
        "template_name": t_name,
        "system_type": "ON_GRID",
        "capacity_kw": 3.00,
        "description": "Standard 3kW On-Grid Residential Rooftop Solution",
        "is_active": True,
        "items": [
            {
                "product_id": panel.id,
                "item_category": panel.category,
                "default_quantity": 6.00,
                "unit_of_measure": "NOS",
                "is_mandatory": True,
            },
            {
                "product_id": inverter.id,
                "item_category": inverter.category,
                "default_quantity": 1.00,
                "unit_of_measure": "NOS",
                "is_mandatory": True,
            },
            {
                "product_id": cable.id,
                "item_category": cable.category,
                "default_quantity": 50.00,
                "unit_of_measure": "MTR",
                "is_mandatory": False,
            },
        ],
    }

    res = client.post("/api/v1/bom/templates", json=payload, headers=admin_headers)
    assert res.status_code == 201, f"Create BOM template failed: {res.text}"
    data = res.json()["data"]
    assert data["template_name"] == t_name
    assert data["system_type"] == "ON_GRID"
    assert data["capacity_kw"] == 3.00
    assert data["is_active"] is True
    assert data["item_count"] == 3
    assert len(data["items"]) == 3
    template_id = data["id"]

    # 2. Duplicate template name rejection (409 Conflict)
    res_dup = client.post("/api/v1/bom/templates", json=payload, headers=admin_headers)
    assert res_dup.status_code == 409
    assert "already exists" in res_dup.json()["detail"]

    # 3. Reject non-existent product ID (404 Not Found)
    bad_payload = {
        "template_name": f"Nonexistent Prod - {uuid.uuid4().hex[:6].upper()}",
        "system_type": "ON_GRID",
        "capacity_kw": 3.00,
        "items": [{"product_id": 99999999, "default_quantity": 1.00}],
    }
    res_bad = client.post("/api/v1/bom/templates", json=bad_payload, headers=admin_headers)
    assert res_bad.status_code == 404

    # 4. Reject inactive product (400 Bad Request)
    inact_payload = {
        "template_name": f"Inactive Prod - {uuid.uuid4().hex[:6].upper()}",
        "system_type": "ON_GRID",
        "capacity_kw": 3.00,
        "items": [{"product_id": inactive_p.id, "default_quantity": 1.00}],
    }
    res_inact = client.post("/api/v1/bom/templates", json=inact_payload, headers=admin_headers)
    assert res_inact.status_code == 400
    assert "inactive" in res_inact.json()["detail"].lower()

    # 5. Reject duplicate products in the same template creation payload (400 Bad Request)
    dup_item_payload = {
        "template_name": f"Dup Item - {uuid.uuid4().hex[:6].upper()}",
        "system_type": "ON_GRID",
        "capacity_kw": 3.00,
        "items": [
            {"product_id": panel.id, "default_quantity": 3.00},
            {"product_id": panel.id, "default_quantity": 3.00},
        ],
    }
    res_dup_item = client.post("/api/v1/bom/templates", json=dup_item_payload, headers=admin_headers)
    assert res_dup_item.status_code == 400
    assert "duplicate" in res_dup_item.json()["detail"].lower()

    # 6. Reject UOM mismatch (400 Bad Request)
    uom_mismatch_payload = {
        "template_name": f"UOM Mismatch - {uuid.uuid4().hex[:6].upper()}",
        "system_type": "ON_GRID",
        "capacity_kw": 3.00,
        "items": [
            {
                "product_id": panel.id,
                "default_quantity": 6.00,
                "unit_of_measure": "MTR",  # panel UOM is NOS
            }
        ],
    }
    res_uom = client.post("/api/v1/bom/templates", json=uom_mismatch_payload, headers=admin_headers)
    assert res_uom.status_code == 400
    assert "uom" in res_uom.json()["detail"].lower()

    # 7. Reject invalid system type (422 Unprocessable)
    bad_st_payload = {
        "template_name": f"Bad System - {uuid.uuid4().hex[:6].upper()}",
        "system_type": "INVALID_TYPE",
        "capacity_kw": 3.00,
    }
    res_st = client.post("/api/v1/bom/templates", json=bad_st_payload, headers=admin_headers)
    assert res_st.status_code == 422

    # 8. Reject zero or negative capacity (422 Unprocessable)
    bad_cap_payload = {
        "template_name": f"Bad Cap - {uuid.uuid4().hex[:6].upper()}",
        "system_type": "ON_GRID",
        "capacity_kw": 0.00,
    }
    res_cap = client.post("/api/v1/bom/templates", json=bad_cap_payload, headers=admin_headers)
    assert res_cap.status_code == 422

    # 9. GET template detail
    res_get = client.get(f"/api/v1/bom/templates/{template_id}", headers=admin_headers)
    assert res_get.status_code == 200
    get_data = res_get.json()["data"]
    assert get_data["id"] == template_id
    assert get_data["item_count"] == 3
    assert len(get_data["items"]) == 3
    assert get_data["items"][0]["unit_price"] is not None

    # 10. PUT update template metadata
    new_desc = "Updated description for test template"
    res_put = client.put(
        f"/api/v1/bom/templates/{template_id}",
        json={"description": new_desc},
        headers=admin_headers,
    )
    assert res_put.status_code == 200
    assert res_put.json()["data"]["description"] == new_desc

    # 11. PATCH status: Deactivate and Reactivate
    res_deact = client.patch(
        f"/api/v1/bom/templates/{template_id}/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert res_deact.status_code == 200
    assert res_deact.json()["data"]["is_active"] is False

    res_react = client.patch(
        f"/api/v1/bom/templates/{template_id}/status",
        json={"is_active": True},
        headers=admin_headers,
    )
    assert res_react.status_code == 200
    assert res_react.json()["data"]["is_active"] is True


# ============================================================
# 2. BOM TEMPLATE LISTING & SEARCH
# ============================================================

def test_bom_template_list_and_search(setup_bom_auth_and_data):
    tokens, _, products, _ = setup_bom_auth_and_data
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}
    panel = products["panel"]

    uniq = uuid.uuid4().hex[:6].upper()
    name_alpha = f"Alpha-{uniq}-Special"
    name_beta = f"Beta-{uniq}-Standard"

    client.post(
        "/api/v1/bom/templates",
        json={
            "template_name": name_alpha,
            "system_type": "HYBRID",
            "capacity_kw": 5.00,
            "is_active": True,
            "items": [{"product_id": panel.id, "default_quantity": 10.00}],
        },
        headers=admin_headers,
    )

    client.post(
        "/api/v1/bom/templates",
        json={
            "template_name": name_beta,
            "system_type": "OFF_GRID",
            "capacity_kw": 2.50,
            "is_active": False,
        },
        headers=admin_headers,
    )

    # 1. Search by name query
    res = client.get(f"/api/v1/bom/templates?search={uniq}", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    items = data["items"]
    names = [it["template_name"] for it in items]
    assert name_alpha in names
    assert name_beta in names

    # 2. Filter by system_type
    res_st = client.get(f"/api/v1/bom/templates?system_type=HYBRID&search={uniq}", headers=admin_headers)
    assert res_st.status_code == 200
    items_st = res_st.json()["data"]["items"]
    assert len(items_st) == 1
    assert items_st[0]["template_name"] == name_alpha

    # 3. Filter by capacity_kw
    res_cap = client.get(f"/api/v1/bom/templates?capacity_kw=2.5&search={uniq}", headers=admin_headers)
    assert res_cap.status_code == 200
    items_cap = res_cap.json()["data"]["items"]
    assert len(items_cap) == 1
    assert items_cap[0]["template_name"] == name_beta

    # 4. Filter by is_active
    res_act = client.get(f"/api/v1/bom/templates?is_active=false&search={uniq}", headers=admin_headers)
    assert res_act.status_code == 200
    items_act = res_act.json()["data"]["items"]
    assert any(it["template_name"] == name_beta for it in items_act)
    assert not any(it["template_name"] == name_alpha for it in items_act)


# ============================================================
# 3. BOM TEMPLATE ITEM MANAGEMENT (ADD, UPDATE, DELETE)
# ============================================================

def test_bom_template_item_management(setup_bom_auth_and_data):
    tokens, _, products, _ = setup_bom_auth_and_data
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}
    panel = products["panel"]
    inverter = products["inverter"]
    cable = products["cable"]
    inactive_p = products["inactive"]

    t_res = client.post(
        "/api/v1/bom/templates",
        json={
            "template_name": f"Item Mgmt Test - {uuid.uuid4().hex[:6].upper()}",
            "system_type": "ON_GRID",
            "capacity_kw": 3.00,
            "items": [{"product_id": panel.id, "default_quantity": 6.00}],
        },
        headers=admin_headers,
    )
    assert t_res.status_code == 201
    template_id = t_res.json()["data"]["id"]

    # 1. Add new item to template
    add_payload = {
        "product_id": inverter.id,
        "item_category": inverter.category,
        "default_quantity": 1.00,
        "unit_of_measure": "NOS",
        "is_mandatory": True,
    }
    add_res = client.post(f"/api/v1/bom/templates/{template_id}/items", json=add_payload, headers=admin_headers)
    assert add_res.status_code == 201
    item_data = add_res.json()["data"]
    assert item_data["product_id"] == inverter.id
    assert item_data["default_quantity"] == 1.00
    new_item_id = item_data["id"]

    # 2. Add duplicate item rejection (409 Conflict)
    dup_res = client.post(f"/api/v1/bom/templates/{template_id}/items", json=add_payload, headers=admin_headers)
    assert dup_res.status_code == 409
    assert "already exists" in dup_res.json()["detail"].lower()

    # 3. Add inactive product rejection (400 Bad Request)
    inact_res = client.post(
        f"/api/v1/bom/templates/{template_id}/items",
        json={"product_id": inactive_p.id, "default_quantity": 2.00},
        headers=admin_headers,
    )
    assert inact_res.status_code == 400

    # 4. Add item with UOM mismatch (400 Bad Request)
    uom_res = client.post(
        f"/api/v1/bom/templates/{template_id}/items",
        json={"product_id": cable.id, "default_quantity": 50.00, "unit_of_measure": "NOS"},  # cable is MTR
        headers=admin_headers,
    )
    assert uom_res.status_code == 400

    # 5. PUT update item default quantity
    put_res = client.put(
        f"/api/v1/bom/templates/{template_id}/items/{new_item_id}",
        json={"default_quantity": 2.00},
        headers=admin_headers,
    )
    assert put_res.status_code == 200
    assert put_res.json()["data"]["default_quantity"] == 2.00

    # 6. DELETE item from template
    del_res = client.delete(f"/api/v1/bom/templates/{template_id}/items/{new_item_id}", headers=admin_headers)
    assert del_res.status_code == 200

    # Verify item is deleted
    t_after = client.get(f"/api/v1/bom/templates/{template_id}", headers=admin_headers).json()["data"]
    assert len(t_after["items"]) == 1
    assert not any(it["id"] == new_item_id for it in t_after["items"])


# ============================================================
# 4. ROLE-BASED ACCESS CONTROL (RBAC)
# ============================================================

def test_bom_rbac_permissions(setup_bom_auth_and_data):
    tokens, _, products, project_id = setup_bom_auth_and_data
    panel = products["panel"]

    def _headers(role):
        return {"Authorization": f"Bearer {tokens[role]}"}

    t_payload = {
        "template_name": f"RBAC Template - {uuid.uuid4().hex[:6].upper()}",
        "system_type": "ON_GRID",
        "capacity_kw": 3.00,
        "items": [{"product_id": panel.id, "default_quantity": 6.00}],
    }

    # 1. SUPER_ADMIN: Can create template (201)
    res_admin = client.post("/api/v1/bom/templates", json=t_payload, headers=_headers(SystemRole.SUPER_ADMIN))
    assert res_admin.status_code == 201
    created_id = res_admin.json()["data"]["id"]

    # 2. TECHNICAL_MANAGER: Can create and update template
    tm_payload = {
        "template_name": f"TM Template - {uuid.uuid4().hex[:6].upper()}",
        "system_type": "ON_GRID",
        "capacity_kw": 3.00,
    }
    res_tm = client.post("/api/v1/bom/templates", json=tm_payload, headers=_headers(SystemRole.TECHNICAL_MANAGER))
    assert res_tm.status_code == 201

    # 3. DIRECTOR: Can read (200), cannot create (403)
    res_dir_get = client.get("/api/v1/bom/templates", headers=_headers(SystemRole.DIRECTOR))
    assert res_dir_get.status_code == 200

    res_dir_post = client.post("/api/v1/bom/templates", json=tm_payload, headers=_headers(SystemRole.DIRECTOR))
    assert res_dir_post.status_code == 403

    # 4. WAREHOUSE_PROCUREMENT: Can read (200), cannot create (403)
    res_wh_get = client.get("/api/v1/bom/templates", headers=_headers(SystemRole.WAREHOUSE_PROCUREMENT))
    assert res_wh_get.status_code == 200

    res_wh_post = client.post("/api/v1/bom/templates", json=tm_payload, headers=_headers(SystemRole.WAREHOUSE_PROCUREMENT))
    assert res_wh_post.status_code == 403

    # 5. SALES: Blocked on both read and manage (403)
    res_sales_get = client.get("/api/v1/bom/templates", headers=_headers(SystemRole.SALES))
    assert res_sales_get.status_code == 403
    res_sales_post = client.post("/api/v1/bom/templates", json=tm_payload, headers=_headers(SystemRole.SALES))
    assert res_sales_post.status_code == 403

    # 6. FIELD_TECHNICIAN: Blocked on all BOM operations (403)
    res_ft_get = client.get("/api/v1/bom/templates", headers=_headers(SystemRole.FIELD_TECHNICIAN))
    assert res_ft_get.status_code == 403
    res_ft_post = client.post("/api/v1/bom/templates", json=tm_payload, headers=_headers(SystemRole.FIELD_TECHNICIAN))
    assert res_ft_post.status_code == 403

    # 7. CUSTOMER: Blocked on all BOM operations (403)
    res_cust_get = client.get("/api/v1/bom/templates", headers=_headers(SystemRole.CUSTOMER))
    assert res_cust_get.status_code == 403
    res_cust_post = client.post("/api/v1/bom/templates", json=tm_payload, headers=_headers(SystemRole.CUSTOMER))
    assert res_cust_post.status_code == 403


# ============================================================
# 5. PROJECT BOM GENERATION & IDEMPOTENCY
# ============================================================

def test_project_bom_generation_and_idempotency(setup_bom_auth_and_data):
    tokens, _, products, project_id = setup_bom_auth_and_data
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}
    panel = products["panel"]
    inverter = products["inverter"]
    cable = products["cable"]

    # 1. Create an inactive template matching system type and capacity
    t_inact_res = client.post(
        "/api/v1/bom/templates",
        json={
            "template_name": f"Inactive 3kW - {uuid.uuid4().hex[:6].upper()}",
            "system_type": "ON_GRID",
            "capacity_kw": 3.00,
            "is_active": False,
            "items": [{"product_id": panel.id, "default_quantity": 6.00}],
        },
        headers=admin_headers,
    )
    inact_template_id = t_inact_res.json()["data"]["id"]

    # Try generating from inactive template (400 Bad Request)
    gen_inact = client.post(
        f"/api/v1/projects/{project_id}/bom/generate",
        json={"template_id": inact_template_id},
        headers=admin_headers,
    )
    assert gen_inact.status_code == 400
    assert "inactive" in gen_inact.json()["detail"].lower()

    # 2. Create template with mismatched system type
    t_mismatch_type = client.post(
        "/api/v1/bom/templates",
        json={
            "template_name": f"Hybrid 3kW - {uuid.uuid4().hex[:6].upper()}",
            "system_type": "HYBRID",
            "capacity_kw": 3.00,
            "items": [{"product_id": panel.id, "default_quantity": 6.00}],
        },
        headers=admin_headers,
    )
    mismatch_type_id = t_mismatch_type.json()["data"]["id"]

    # Try generating from mismatched system type (400 Bad Request)
    gen_type_res = client.post(
        f"/api/v1/projects/{project_id}/bom/generate",
        json={"template_id": mismatch_type_id},
        headers=admin_headers,
    )
    assert gen_type_res.status_code == 400
    assert "system type" in gen_type_res.json()["detail"].lower()

    # 3. Create template with mismatched capacity (5.0 kW vs project's 3.0 kW)
    t_mismatch_cap = client.post(
        "/api/v1/bom/templates",
        json={
            "template_name": f"OnGrid 5kW - {uuid.uuid4().hex[:6].upper()}",
            "system_type": "ON_GRID",
            "capacity_kw": 5.00,
            "items": [{"product_id": panel.id, "default_quantity": 10.00}],
        },
        headers=admin_headers,
    )
    mismatch_cap_id = t_mismatch_cap.json()["data"]["id"]

    # Try generating from mismatched capacity (400 Bad Request)
    gen_cap_res = client.post(
        f"/api/v1/projects/{project_id}/bom/generate",
        json={"template_id": mismatch_cap_id},
        headers=admin_headers,
    )
    assert gen_cap_res.status_code == 400
    assert "capacity" in gen_cap_res.json()["detail"].lower()

    # 4. Create fully matching active template
    t_valid = client.post(
        "/api/v1/bom/templates",
        json={
            "template_name": f"Valid 3kW Match - {uuid.uuid4().hex[:6].upper()}",
            "system_type": "ON_GRID",
            "capacity_kw": 3.00,
            "items": [
                {"product_id": panel.id, "default_quantity": 6.00, "unit_of_measure": "NOS"},
                {"product_id": inverter.id, "default_quantity": 1.00, "unit_of_measure": "NOS"},
                {"product_id": cable.id, "default_quantity": 40.00, "unit_of_measure": "MTR"},
            ],
        },
        headers=admin_headers,
    )
    valid_template_id = t_valid.json()["data"]["id"]

    # 5. Successfully generate project BOM
    gen_res = client.post(
        f"/api/v1/projects/{project_id}/bom/generate",
        json={"template_id": valid_template_id},
        headers=admin_headers,
    )
    assert gen_res.status_code == 201, f"BOM generation failed: {gen_res.text}"
    gen_data = gen_res.json()["data"]
    assert gen_data["project_id"] == project_id
    assert gen_data["total_items"] == 3
    assert len(gen_data["items"]) == 3

    # Verify unit cost snapshot matches product base_price
    for item in gen_data["items"]:
        if item["product_id"] == panel.id:
            assert item["unit_cost_snapshot"] == float(panel.base_price)
            assert item["planned_quantity"] == 6.00
            assert item["allocated_quantity"] == 0.00
            assert item["dispatched_quantity"] == 0.00
            assert item["installed_quantity"] == 0.00
        elif item["product_id"] == inverter.id:
            assert item["unit_cost_snapshot"] == float(inverter.base_price)
            assert item["planned_quantity"] == 1.00
        elif item["product_id"] == cable.id:
            assert item["unit_cost_snapshot"] == float(cable.base_price)
            assert item["planned_quantity"] == 40.00

    # 6. IDEMPOTENCY CHECK: Attempt generating again on project with existing BOM (409 Conflict)
    gen_dup = client.post(
        f"/api/v1/projects/{project_id}/bom/generate",
        json={"template_id": valid_template_id},
        headers=admin_headers,
    )
    assert gen_dup.status_code == 409
    assert "already contains" in gen_dup.json()["detail"]

    # 7. GET /projects/{project_id}/bom listing
    get_proj_bom = client.get(f"/api/v1/projects/{project_id}/bom", headers=admin_headers)
    assert get_proj_bom.status_code == 200
    p_bom_data = get_proj_bom.json()["data"]
    assert p_bom_data["project_id"] == project_id
    assert len(p_bom_data["items"]) == 3
    assert p_bom_data["total_estimated_cost"] > 0


# ============================================================
# 6. PROJECT BOM ITEM QUANTITY UPDATE & PRECEDENCE INVARIANT
# ============================================================

def test_project_bom_item_quantity_update(setup_bom_auth_and_data):
    tokens, _, _, project_id = setup_bom_auth_and_data
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}

    # Fetch existing project BOM items
    bom_res = client.get(f"/api/v1/projects/{project_id}/bom", headers=admin_headers)
    assert bom_res.status_code == 200
    items = bom_res.json()["data"]["items"]
    target_item = items[0]
    item_id = target_item["id"]

    # 1. Update planned quantity to valid higher quantity (e.g. 8.00)
    update_res = client.put(
        f"/api/v1/projects/{project_id}/bom/items/{item_id}",
        json={"planned_quantity": 8.00},
        headers=admin_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["planned_quantity"] == 8.00

    # 2. Simulate allocated_quantity = 5.00 directly in DB
    with SessionLocal() as db:
        db_item = db.execute(select(ProjectBomItem).where(ProjectBomItem.id == item_id)).scalar_one()
        db_item.allocated_quantity = Decimal("5.00")
        db.commit()

    # 3. Attempt to update planned quantity < allocated_quantity (e.g. 4.00 < 5.00) -> 400 Bad Request
    fail_res = client.put(
        f"/api/v1/projects/{project_id}/bom/items/{item_id}",
        json={"planned_quantity": 4.00},
        headers=admin_headers,
    )
    assert fail_res.status_code == 400
    assert "allocated" in fail_res.json()["detail"].lower()

    # 4. Update planned quantity >= allocated_quantity (e.g. 6.00 >= 5.00) -> 200 OK
    ok_res = client.put(
        f"/api/v1/projects/{project_id}/bom/items/{item_id}",
        json={"planned_quantity": 6.00},
        headers=admin_headers,
    )
    assert ok_res.status_code == 200
    assert ok_res.json()["data"]["planned_quantity"] == 6.00
    assert ok_res.json()["data"]["allocated_quantity"] == 5.00


# ============================================================
# 7. AUDIT LOGGING VERIFICATION
# ============================================================

def test_bom_audit_logging(setup_bom_auth_and_data):
    tokens, user_ids, products, project_id = setup_bom_auth_and_data
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}
    admin_id = user_ids[SystemRole.SUPER_ADMIN]
    panel = products["panel"]

    audit_t_name = f"Audit Template - {uuid.uuid4().hex[:6].upper()}"

    # 1. Create template (triggers BOM_TEMPLATE CREATE)
    c_res = client.post(
        "/api/v1/bom/templates",
        json={
            "template_name": audit_t_name,
            "system_type": "ON_GRID",
            "capacity_kw": 3.00,
            "items": [{"product_id": panel.id, "default_quantity": 6.00}],
        },
        headers=admin_headers,
    )
    assert c_res.status_code == 201
    t_id = c_res.json()["data"]["id"]

    # 2. Update template (triggers BOM_TEMPLATE UPDATE)
    u_res = client.put(
        f"/api/v1/bom/templates/{t_id}",
        json={"description": "Audit updated"},
        headers=admin_headers,
    )
    assert u_res.status_code == 200

    # 3. Status change (triggers BOM_TEMPLATE STATUS_CHANGE)
    s_res = client.patch(
        f"/api/v1/bom/templates/{t_id}/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert s_res.status_code == 200

    # Verify AuditLog entries in DB
    with SessionLocal() as db:
        t_logs = db.execute(
            select(AuditLog)
            .where(AuditLog.entity_name == "BOM_TEMPLATE", AuditLog.entity_id == t_id)
            .order_by(AuditLog.created_at.asc())
        ).scalars().all()

        t_actions = [l.action for l in t_logs]
        assert "CREATE" in t_actions
        assert "UPDATE" in t_actions
        assert "DEACTIVATE" in t_actions

        for l in t_logs:
            assert l.user_id == admin_id

        # Verify PROJECT_BOM logs for project_id
        p_logs = db.execute(
            select(AuditLog)
            .where(AuditLog.entity_name == "PROJECT_BOM", AuditLog.entity_id == project_id)
            .order_by(AuditLog.created_at.asc())
        ).scalars().all()

        p_actions = [l.action for l in p_logs]
        assert "BOM_GENERATE" in p_actions
        assert "PLANNED_QTY_UPDATE" in p_actions
