import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from decimal import Decimal
from datetime import date, timedelta
import uuid

from app.main import app
from app.database import SessionLocal
from app.models.auth import User, Role
from app.models.crm import Product
from app.models.projects import (
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
    GoodsReceipt,
    GoodsReceiptItem,
    Project,
    ProjectBomItem,
)
from app.models.inventory import Inventory, StockMovement, SerialNumber
from app.utils.roles import SystemRole
from app.utils.security import hash_password, create_access_token

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_procurement_test_env():
    tokens = {}
    user_ids = {}

    with SessionLocal() as db:
        role_slugs = [
            SystemRole.SUPER_ADMIN,
            SystemRole.WAREHOUSE_PROCUREMENT,
            SystemRole.DIRECTOR,
            SystemRole.TECHNICAL_MANAGER,
            SystemRole.SALES,
            SystemRole.FINANCE_ACCOUNTS,
            SystemRole.FIELD_TECHNICIAN,
            SystemRole.SERVICE_WARRANTY,
            SystemRole.CUSTOMER,
        ]

        for slug in role_slugs:
            role_obj = db.execute(select(Role).where(Role.slug == slug)).scalar_one()
            email = f"test_{slug.lower()}_proc@sunpower.com"
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if not user:
                user = User(
                    role_id=role_obj.id,
                    email=email,
                    full_name=f"Test {slug} Proc",
                    hashed_password=hash_password("Pass123!Safe"),
                    is_active=True,
                    is_verified=True,
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            tokens[slug] = create_access_token(
                data={"sub": str(user.id), "role": role_obj.slug, "email": user.email}
            )
            user_ids[slug] = user.id

        # Find or create a non-serialized product for tests
        non_ser_prod = db.execute(
            select(Product).where(Product.is_serialized == False, Product.is_active == True)
        ).scalars().first()
        if not non_ser_prod:
            non_ser_prod = Product(
                product_code=f"TEST-CABLE-{uuid.uuid4().hex[:6].upper()}",
                name="Solar DC Cable 4sqmm Test",
                category="CABLES",
                unit_of_measure="METERS",
                is_serialized=False,
                base_price=Decimal("45.00"),
                tax_rate_percent=Decimal("18.00"),
                min_stock_alert=Decimal("100.00"),
                is_active=True,
            )
            db.add(non_ser_prod)
            db.commit()
            db.refresh(non_ser_prod)

        # Find or create a serialized product for tests
        ser_prod = db.execute(
            select(Product).where(Product.is_serialized == True, Product.is_active == True)
        ).scalars().first()
        if not ser_prod:
            ser_prod = Product(
                product_code=f"TEST-INV-{uuid.uuid4().hex[:6].upper()}",
                name="Solar Inverter 5kW Test",
                category="INVERTER",
                unit_of_measure="NOS",
                is_serialized=True,
                base_price=Decimal("45000.00"),
                tax_rate_percent=Decimal("12.00"),
                min_stock_alert=Decimal("2.00"),
                is_active=True,
            )
            db.add(ser_prod)
            db.commit()
            db.refresh(ser_prod)

        # Find a project for shortage testing
        project = db.execute(select(Project)).scalars().first()

    return {
        "tokens": tokens,
        "user_ids": user_ids,
        "non_ser_prod_id": non_ser_prod.id,
        "ser_prod_id": ser_prod.id,
        "project_id": project.id if project else None,
    }


# ==========================================
# 1. SUPPLIER TESTS
# ==========================================

def test_supplier_crud_and_uniqueness(setup_procurement_test_env):
    env = setup_procurement_test_env
    token = env["tokens"][SystemRole.WAREHOUSE_PROCUREMENT]
    headers = {"Authorization": f"Bearer {token}"}

    uid = uuid.uuid4().hex[:6].upper()
    supplier_payload = {
        "supplier_code": f"SUP-TEST-{uid}",
        "company_name": f"Adani Solar Supplies {uid}",
        "contact_person": "Ramesh Patel",
        "email": f"ramesh_{uid.lower()}@adanisolar.com",
        "phone": "+91 98765 43210",
        "address": "Plot 42, GIDC Electronic Estate",
        "city": "Gandhinagar",
        "state": "Gujarat",
        "gst_number": f"24AAACA{uid}1Z5",
        "pan_number": f"AAACA{uid}",
        "bank_account_details": "HDFC Bank, A/C: 50200012345678, IFSC: HDFC0001234",
    }

    # 1. Create Supplier
    res = client.post("/api/v1/suppliers", json=supplier_payload, headers=headers)
    assert res.status_code == 201, res.text
    created = res.json()["data"]
    supp_id = created["id"]
    assert created["company_name"] == supplier_payload["company_name"]
    assert created["supplier_code"] == supplier_payload["supplier_code"]
    assert created["is_active"] is True

    # 2. Duplicate Company Name -> 409
    dup_res = client.post(
        "/api/v1/suppliers",
        json={**supplier_payload, "supplier_code": f"SUP-OTHER-{uid}", "gst_number": None},
        headers=headers,
    )
    assert dup_res.status_code == 409
    assert "already exists" in dup_res.json()["detail"].lower()

    # 3. Duplicate GST -> 409
    dup_gst_res = client.post(
        "/api/v1/suppliers",
        json={**supplier_payload, "company_name": f"Different Name {uid}", "supplier_code": f"SUP-OTH2-{uid}"},
        headers=headers,
    )
    assert dup_gst_res.status_code == 409
    assert "already registered" in dup_gst_res.json()["detail"].lower()

    # 4. List Suppliers
    list_res = client.get(f"/api/v1/suppliers?search={uid}", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]["items"]) >= 1

    # 5. Get Supplier Detail
    detail_res = client.get(f"/api/v1/suppliers/{supp_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["data"]["bank_account_details"] == supplier_payload["bank_account_details"]

    # 6. Update Supplier
    upd_res = client.put(
        f"/api/v1/suppliers/{supp_id}",
        json={"contact_person": "Suresh Patel", "phone": "+91 91234 56789"},
        headers=headers,
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["data"]["contact_person"] == "Suresh Patel"

    # 7. Status Toggle (Deactivate / Activate)
    toggle_res = client.patch(f"/api/v1/suppliers/{supp_id}/status", json={"is_active": False}, headers=headers)
    assert toggle_res.status_code == 200
    assert toggle_res.json()["data"]["is_active"] is False

    reactivate_res = client.patch(f"/api/v1/suppliers/{supp_id}/status", json={"is_active": True}, headers=headers)
    assert reactivate_res.status_code == 200
    assert reactivate_res.json()["data"]["is_active"] is True


def test_supplier_rbac(setup_procurement_test_env):
    env = setup_procurement_test_env
    super_admin_token = env["tokens"][SystemRole.SUPER_ADMIN]
    director_token = env["tokens"][SystemRole.DIRECTOR]
    sales_token = env["tokens"][SystemRole.SALES]
    customer_token = env["tokens"][SystemRole.CUSTOMER]

    uid = uuid.uuid4().hex[:6].upper()
    payload = {
        "company_name": f"RBAC Supplier {uid}",
        "contact_person": "Contact Person",
        "email": f"rbac_{uid}@supplier.com",
        "phone": "+91 99999 88888",
        "address": "Industrial Area",
        "city": "Bengaluru",
        "state": "Karnataka",
    }

    # SUPER_ADMIN can create
    res_sa = client.post("/api/v1/suppliers", json=payload, headers={"Authorization": f"Bearer {super_admin_token}"})
    assert res_sa.status_code == 201

    # DIRECTOR can read
    res_dir = client.get("/api/v1/suppliers", headers={"Authorization": f"Bearer {director_token}"})
    assert res_dir.status_code == 200

    # DIRECTOR cannot create (write requires suppliers.manage)
    res_dir_post = client.post("/api/v1/suppliers", json={**payload, "company_name": f"Dir {uid}"}, headers={"Authorization": f"Bearer {director_token}"})
    assert res_dir_post.status_code == 403

    # SALES forbidden (both read & write)
    res_sales = client.get("/api/v1/suppliers", headers={"Authorization": f"Bearer {sales_token}"})
    assert res_sales.status_code == 403

    # CUSTOMER forbidden
    res_cust = client.get("/api/v1/suppliers", headers={"Authorization": f"Bearer {customer_token}"})
    assert res_cust.status_code == 403


# ==========================================
# 2. PURCHASE ORDER TESTS
# ==========================================

def test_purchase_order_creation_and_calculation(setup_procurement_test_env):
    env = setup_procurement_test_env
    token = env["tokens"][SystemRole.WAREHOUSE_PROCUREMENT]
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = env["non_ser_prod_id"]

    # Create active supplier
    uid = uuid.uuid4().hex[:6].upper()
    supp_res = client.post(
        "/api/v1/suppliers",
        json={
            "company_name": f"PO Calc Supplier {uid}",
            "contact_person": "Manager",
            "email": f"supp_{uid}@calc.com",
            "phone": "+91 98765 11111",
            "address": "Phase 1, MIDC",
            "city": "Pune",
            "state": "Maharashtra",
        },
        headers=headers,
    )
    supplier_id = supp_res.json()["data"]["id"]

    po_payload = {
        "supplier_id": supplier_id,
        "po_date": str(date.today()),
        "expected_delivery_date": str(date.today() + timedelta(days=7)),
        "notes": "Urgent procurement of cables",
        "items": [
            {
                "product_id": prod_id,
                "ordered_quantity": 100,
                "unit_price": 45.00,
                "tax_rate_percent": 18.00,
            }
        ],
    }

    # 1. Create PO
    res = client.post("/api/v1/purchase-orders", json=po_payload, headers=headers)
    assert res.status_code == 201, res.text
    po_data = res.json()["data"]

    # Verify calculation: 100 * 45 = 4500 subtotal, 18% tax = 810, total = 5310
    assert po_data["status"] == "DRAFT"
    assert Decimal(str(po_data["tax_amount"])) == Decimal("810.00")
    assert Decimal(str(po_data["total_amount"])) == Decimal("5310.00")
    assert po_data["po_number"].startswith(f"PO-{date.today().year}-")

    # 2. Rejection of inactive supplier
    client.patch(f"/api/v1/suppliers/{supplier_id}/status", json={"is_active": False}, headers=headers)
    inactive_res = client.post("/api/v1/purchase-orders", json=po_payload, headers=headers)
    assert inactive_res.status_code == 400
    assert "inactive" in inactive_res.json()["detail"].lower()


def test_purchase_order_lifecycle(setup_procurement_test_env):
    env = setup_procurement_test_env
    token = env["tokens"][SystemRole.WAREHOUSE_PROCUREMENT]
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = env["non_ser_prod_id"]

    # Create supplier
    uid = uuid.uuid4().hex[:6].upper()
    supp_res = client.post(
        "/api/v1/suppliers",
        json={
            "company_name": f"PO Life Supplier {uid}",
            "contact_person": "Lead",
            "email": f"supp_{uid}@life.com",
            "phone": "+91 98765 22222",
            "address": "Sector 18",
            "city": "Noida",
            "state": "Uttar Pradesh",
        },
        headers=headers,
    )
    supplier_id = supp_res.json()["data"]["id"]

    # Create DRAFT PO
    res = client.post(
        "/api/v1/purchase-orders",
        json={
            "supplier_id": supplier_id,
            "po_date": str(date.today()),
            "items": [{"product_id": prod_id, "ordered_quantity": 50, "unit_price": 40.00, "tax_rate_percent": 12.00}],
        },
        headers=headers,
    )
    po_id = res.json()["data"]["id"]

    # 1. Edit DRAFT PO (allowed)
    edit_res = client.put(
        f"/api/v1/purchase-orders/{po_id}",
        json={"notes": "Updated instructions", "items": [{"product_id": prod_id, "ordered_quantity": 60, "unit_price": 40.00, "tax_rate_percent": 12.00}]},
        headers=headers,
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["data"]["notes"] == "Updated instructions"
    assert Decimal(str(edit_res.json()["data"]["total_amount"])) == Decimal("2688.00")  # 60 * 40 * 1.12 = 2688.00

    # 2. Issue PO
    issue_res = client.post(f"/api/v1/purchase-orders/{po_id}/issue", headers=headers)
    assert issue_res.status_code == 200
    assert issue_res.json()["data"]["status"] == "ISSUED"

    # 3. Edit after issue (strictly rejected)
    post_issue_edit = client.put(f"/api/v1/purchase-orders/{po_id}", json={"notes": "Illegal edit"}, headers=headers)
    assert post_issue_edit.status_code == 400
    assert "only draft" in post_issue_edit.json()["detail"].lower()

    # 4. Cancel PO before receipt (allowed)
    cancel_res = client.post(f"/api/v1/purchase-orders/{po_id}/cancel", headers=headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["status"] == "CANCELLED"


# ==========================================
# 3. GOODS RECEIPT (GRN) & INVENTORY TESTS
# ==========================================

def test_goods_receipt_full_and_partial_atomic_inward(setup_procurement_test_env):
    env = setup_procurement_test_env
    token = env["tokens"][SystemRole.WAREHOUSE_PROCUREMENT]
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = env["non_ser_prod_id"]

    # Create supplier & issued PO for 100 units at 50.00
    uid = uuid.uuid4().hex[:6].upper()
    supp_res = client.post(
        "/api/v1/suppliers",
        json={
            "company_name": f"GRN Inward Supplier {uid}",
            "contact_person": "Inspector",
            "email": f"supp_{uid}@inward.com",
            "phone": "+91 98765 33333",
            "address": "Industrial Corridor",
            "city": "Chennai",
            "state": "Tamil Nadu",
        },
        headers=headers,
    )
    supplier_id = supp_res.json()["data"]["id"]

    po_res = client.post(
        "/api/v1/purchase-orders",
        json={
            "supplier_id": supplier_id,
            "po_date": str(date.today()),
            "items": [{"product_id": prod_id, "ordered_quantity": 100, "unit_price": 50.00, "tax_rate_percent": 12.00}],
        },
        headers=headers,
    )
    po_id = po_res.json()["data"]["id"]
    po_item_id = po_res.json()["data"]["items"][0]["id"]

    # Issue PO
    client.post(f"/api/v1/purchase-orders/{po_id}/issue", headers=headers)

    # 1. Partial Receipt: 40 units accepted
    grn_payload_1 = {
        "purchase_order_id": po_id,
        "received_date": str(date.today()),
        "challan_number": f"CHALLAN-P1-{uid}",
        "inspection_remarks": "First batch of 40 units received in good condition",
        "items": [
            {
                "po_item_id": po_item_id,
                "product_id": prod_id,
                "received_quantity": 40,
                "accepted_quantity": 40,
                "rejected_quantity": 0,
            }
        ],
    }

    res_grn1 = client.post("/api/v1/goods-receipts", json=grn_payload_1, headers=headers)
    assert res_grn1.status_code == 201, res_grn1.text
    grn1_data = res_grn1.json()["data"]
    assert grn1_data["status"] == "ACCEPTED"
    assert grn1_data["grn_number"].startswith(f"GRN-{date.today().year}-")

    # Verify PO status moved to PARTIALLY_RECEIVED
    po_check_1 = client.get(f"/api/v1/purchase-orders/{po_id}", headers=headers).json()["data"]
    assert po_check_1["status"] == "PARTIALLY_RECEIVED"
    assert Decimal(str(po_check_1["items"][0]["received_quantity"])) == Decimal("40.00")

    # Verify Inventory balances & valuation
    inv_check = client.get(f"/api/v1/inventory?search={po_check_1['items'][0]['product_code']}", headers=headers).json()["data"]
    matched_inv = next(i for i in inv_check["items"] if i["product_id"] == prod_id)
    assert Decimal(str(matched_inv["quantity_on_hand"])) >= Decimal("40.00")
    assert Decimal(str(matched_inv["quantity_available"])) >= Decimal("40.00")

    # 2. Second Receipt: Remaining 60 units accepted
    grn_payload_2 = {
        "purchase_order_id": po_id,
        "received_date": str(date.today()),
        "challan_number": f"CHALLAN-P2-{uid}",
        "inspection_remarks": "Second batch completing PO",
        "items": [
            {
                "po_item_id": po_item_id,
                "product_id": prod_id,
                "received_quantity": 60,
                "accepted_quantity": 60,
                "rejected_quantity": 0,
            }
        ],
    }

    res_grn2 = client.post("/api/v1/goods-receipts", json=grn_payload_2, headers=headers)
    assert res_grn2.status_code == 201

    # Verify PO status moved to RECEIVED
    po_check_2 = client.get(f"/api/v1/purchase-orders/{po_id}", headers=headers).json()["data"]
    assert po_check_2["status"] == "RECEIVED"
    assert Decimal(str(po_check_2["items"][0]["received_quantity"])) == Decimal("100.00")


def test_goods_receipt_rejections_and_balance_constraint(setup_procurement_test_env):
    env = setup_procurement_test_env
    token = env["tokens"][SystemRole.WAREHOUSE_PROCUREMENT]
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = env["non_ser_prod_id"]

    uid = uuid.uuid4().hex[:6].upper()
    supp_res = client.post(
        "/api/v1/suppliers",
        json={"company_name": f"Rejection Supp {uid}", "contact_person": "QA", "email": f"supp_{uid}@rej.com", "phone": "+91 98765 44444", "address": "Hub", "city": "Jaipur", "state": "Rajasthan"},
        headers=headers,
    )
    supplier_id = supp_res.json()["data"]["id"]

    po_res = client.post(
        "/api/v1/purchase-orders",
        json={"supplier_id": supplier_id, "po_date": str(date.today()), "items": [{"product_id": prod_id, "ordered_quantity": 50, "unit_price": 50.00}]},
        headers=headers,
    )
    po_id = po_res.json()["data"]["id"]
    po_item_id = po_res.json()["data"]["items"][0]["id"]
    client.post(f"/api/v1/purchase-orders/{po_id}/issue", headers=headers)

    # 1. Violation of received = accepted + rejected constraint (received=30, accepted=20, rejected=5 -> sum=25 != 30)
    invalid_balance = {
        "purchase_order_id": po_id,
        "items": [{"po_item_id": po_item_id, "product_id": prod_id, "received_quantity": 30, "accepted_quantity": 20, "rejected_quantity": 5}],
    }
    res_inv = client.post("/api/v1/goods-receipts", json=invalid_balance, headers=headers)
    assert res_inv.status_code == 400
    assert "must equal accepted" in res_inv.json()["detail"].lower()

    # 2. Missing rejection reason when rejected_quantity > 0
    missing_reason = {
        "purchase_order_id": po_id,
        "items": [{"po_item_id": po_item_id, "product_id": prod_id, "received_quantity": 30, "accepted_quantity": 20, "rejected_quantity": 10, "rejection_reason": ""}],
    }
    res_miss = client.post("/api/v1/goods-receipts", json=missing_reason, headers=headers)
    assert res_miss.status_code == 400
    assert "mandatory" in res_miss.json()["detail"].lower()

    # 3. Valid receipt with rejection: 20 accepted, 10 rejected with reason
    valid_rejection = {
        "purchase_order_id": po_id,
        "received_date": str(date.today()),
        "challan_number": f"CHALLAN-REJ-{uid}",
        "items": [
            {
                "po_item_id": po_item_id,
                "product_id": prod_id,
                "received_quantity": 30,
                "accepted_quantity": 20,
                "rejected_quantity": 10,
                "rejection_reason": "Damaged packaging and dented cable drums",
            }
        ],
    }
    res_valid = client.post("/api/v1/goods-receipts", json=valid_rejection, headers=headers)
    assert res_valid.status_code == 201
    grn_data = res_valid.json()["data"]
    assert grn_data["status"] == "PARTIALLY_ACCEPTED"

    # Verify PO item received_quantity increased only by accepted quantity (20, NOT 30)
    po_check = client.get(f"/api/v1/purchase-orders/{po_id}", headers=headers).json()["data"]
    assert Decimal(str(po_check["items"][0]["received_quantity"])) == Decimal("20.00")


def test_over_receipt_rejection(setup_procurement_test_env):
    env = setup_procurement_test_env
    token = env["tokens"][SystemRole.WAREHOUSE_PROCUREMENT]
    headers = {"Authorization": f"Bearer {token}"}
    prod_id = env["non_ser_prod_id"]

    uid = uuid.uuid4().hex[:6].upper()
    supp_res = client.post(
        "/api/v1/suppliers",
        json={"company_name": f"OverRec Supp {uid}", "contact_person": "QA", "email": f"supp_{uid}@over.com", "phone": "+91 98765 55555", "address": "Hub", "city": "Kolkata", "state": "West Bengal"},
        headers=headers,
    )
    supplier_id = supp_res.json()["data"]["id"]

    po_res = client.post(
        "/api/v1/purchase-orders",
        json={"supplier_id": supplier_id, "po_date": str(date.today()), "items": [{"product_id": prod_id, "ordered_quantity": 10, "unit_price": 100.00}]},
        headers=headers,
    )
    po_id = po_res.json()["data"]["id"]
    po_item_id = po_res.json()["data"]["items"][0]["id"]
    client.post(f"/api/v1/purchase-orders/{po_id}/issue", headers=headers)

    # Attempt to accept 15 units when only 10 were ordered
    over_payload = {
        "purchase_order_id": po_id,
        "items": [{"po_item_id": po_item_id, "product_id": prod_id, "received_quantity": 15, "accepted_quantity": 15, "rejected_quantity": 0}],
    }
    res_over = client.post("/api/v1/goods-receipts", json=over_payload, headers=headers)
    assert res_over.status_code == 400
    assert "over-receipt rejected" in res_over.json()["detail"].lower()


# ==========================================
# 4. WEIGHTED AVERAGE COST TEST
# ==========================================

def test_weighted_average_unit_cost_calculation(setup_procurement_test_env):
    env = setup_procurement_test_env
    token = env["tokens"][SystemRole.WAREHOUSE_PROCUREMENT]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a fresh isolated test product
    uid = uuid.uuid4().hex[:6].upper()
    with SessionLocal() as db:
        cost_prod = Product(
            product_code=f"COST-TEST-{uid}",
            name=f"Cost Test Product {uid}",
            category="STRUCTURE",
            unit_of_measure="NOS",
            is_serialized=False,
            base_price=Decimal("100.00"),
            tax_rate_percent=Decimal("18.00"),
            min_stock_alert=Decimal("5.00"),
            is_active=True,
        )
        db.add(cost_prod)
        db.commit()
        db.refresh(cost_prod)
        cost_prod_id = cost_prod.id

    supp_res = client.post(
        "/api/v1/suppliers",
        json={"company_name": f"Cost Supp {uid}", "contact_person": "Finance", "email": f"supp_{uid}@cost.com", "phone": "+91 98765 66666", "address": "Hub", "city": "Indore", "state": "Madhya Pradesh"},
        headers=headers,
    )
    supplier_id = supp_res.json()["data"]["id"]

    # PO 1: 10 units at 100.00
    po1_res = client.post(
        "/api/v1/purchase-orders",
        json={"supplier_id": supplier_id, "items": [{"product_id": cost_prod_id, "ordered_quantity": 10, "unit_price": 100.00}]},
        headers=headers,
    )
    po1_id = po1_res.json()["data"]["id"]
    po1_item_id = po1_res.json()["data"]["items"][0]["id"]
    client.post(f"/api/v1/purchase-orders/{po1_id}/issue", headers=headers)

    # GRN 1: Inward 10 units at 100.00
    client.post(
        "/api/v1/goods-receipts",
        json={"purchase_order_id": po1_id, "items": [{"po_item_id": po1_item_id, "product_id": cost_prod_id, "received_quantity": 10, "accepted_quantity": 10, "rejected_quantity": 0}]},
        headers=headers,
    )

    # Verify inventory average cost = 100.00
    with SessionLocal() as db:
        inv1 = db.execute(select(Inventory).where(Inventory.product_id == cost_prod_id)).scalar_one()
        assert inv1.quantity_on_hand == Decimal("10.00")
        assert inv1.average_unit_cost == Decimal("100.00")

    # PO 2: 10 units at 140.00
    po2_res = client.post(
        "/api/v1/purchase-orders",
        json={"supplier_id": supplier_id, "items": [{"product_id": cost_prod_id, "ordered_quantity": 10, "unit_price": 140.00}]},
        headers=headers,
    )
    po2_id = po2_res.json()["data"]["id"]
    po2_item_id = po2_res.json()["data"]["items"][0]["id"]
    client.post(f"/api/v1/purchase-orders/{po2_id}/issue", headers=headers)

    # GRN 2: Inward 10 units at 140.00
    # Expected: ((10 * 100) + (10 * 140)) / (10 + 10) = (1000 + 1400) / 20 = 2400 / 20 = 120.00
    client.post(
        "/api/v1/goods-receipts",
        json={"purchase_order_id": po2_id, "items": [{"po_item_id": po2_item_id, "product_id": cost_prod_id, "received_quantity": 10, "accepted_quantity": 10, "rejected_quantity": 0}]},
        headers=headers,
    )

    with SessionLocal() as db:
        inv2 = db.execute(select(Inventory).where(Inventory.product_id == cost_prod_id)).scalar_one()
        assert inv2.quantity_on_hand == Decimal("20.00")
        assert inv2.average_unit_cost == Decimal("120.00")
        assert inv2.quantity_available == Decimal("20.00")


# ==========================================
# 5. SERIALIZED PRODUCT GRN TRACKING
# ==========================================

def test_serialized_product_grn_tracking(setup_procurement_test_env):
    env = setup_procurement_test_env
    token = env["tokens"][SystemRole.WAREHOUSE_PROCUREMENT]
    headers = {"Authorization": f"Bearer {token}"}
    ser_prod_id = env["ser_prod_id"]

    uid = uuid.uuid4().hex[:6].upper()
    supp_res = client.post(
        "/api/v1/suppliers",
        json={"company_name": f"Serial Supp {uid}", "contact_person": "QA", "email": f"supp_{uid}@ser.com", "phone": "+91 98765 77777", "address": "Hub", "city": "Hyderabad", "state": "Telangana"},
        headers=headers,
    )
    supplier_id = supp_res.json()["data"]["id"]

    po_res = client.post(
        "/api/v1/purchase-orders",
        json={"supplier_id": supplier_id, "items": [{"product_id": ser_prod_id, "ordered_quantity": 2, "unit_price": 45000.00}]},
        headers=headers,
    )
    po_id = po_res.json()["data"]["id"]
    po_item_id = po_res.json()["data"]["items"][0]["id"]
    client.post(f"/api/v1/purchase-orders/{po_id}/issue", headers=headers)

    sn1 = f"SN-INV-{uid}-001"
    sn2 = f"SN-INV-{uid}-002"

    # 1. Missing serials when product is serialized (ordered 2, serials=[])
    missing_serials = {
        "purchase_order_id": po_id,
        "items": [{"po_item_id": po_item_id, "product_id": ser_prod_id, "received_quantity": 2, "accepted_quantity": 2, "rejected_quantity": 0, "serial_numbers": []}],
    }
    res_miss = client.post("/api/v1/goods-receipts", json=missing_serials, headers=headers)
    assert res_miss.status_code == 400
    assert "requires exactly 2 serial numbers" in res_miss.json()["detail"].lower()

    # 2. Duplicate serial within request
    dup_serials = {
        "purchase_order_id": po_id,
        "items": [{"po_item_id": po_item_id, "product_id": ser_prod_id, "received_quantity": 2, "accepted_quantity": 2, "rejected_quantity": 0, "serial_numbers": [sn1, sn1]}],
    }
    res_dup = client.post("/api/v1/goods-receipts", json=dup_serials, headers=headers)
    assert res_dup.status_code == 400
    assert "duplicate serial numbers" in res_dup.json()["detail"].lower()

    # 3. Valid receipt with unique serials
    valid_serials = {
        "purchase_order_id": po_id,
        "received_date": str(date.today()),
        "items": [{"po_item_id": po_item_id, "product_id": ser_prod_id, "received_quantity": 2, "accepted_quantity": 2, "rejected_quantity": 0, "serial_numbers": [sn1, sn2]}],
    }
    res_valid = client.post("/api/v1/goods-receipts", json=valid_serials, headers=headers)
    assert res_valid.status_code == 201

    # Verify serials registered in DB with status IN_STOCK
    with SessionLocal() as db:
        registered = db.execute(select(SerialNumber).where(SerialNumber.serial_number.in_([sn1, sn2]))).scalars().all()
        assert len(registered) == 2
        for r in registered:
            assert r.status == "IN_STOCK"
            assert r.purchase_order_id == po_id

    # 4. Query serials endpoint
    serials_res = client.get(f"/api/v1/inventory/{ser_prod_id}/serials", headers=headers)
    assert serials_res.status_code == 200
    assert any(s["serial_number"] == sn1 for s in serials_res.json()["data"]["items"])


# ==========================================
# 6. INVENTORY & SHORTAGES TESTS
# ==========================================

def test_inventory_and_shortages_endpoints(setup_procurement_test_env):
    env = setup_procurement_test_env
    token = env["tokens"][SystemRole.WAREHOUSE_PROCUREMENT]
    headers = {"Authorization": f"Bearer {token}"}
    project_id = env["project_id"]

    # 1. List inventory
    inv_res = client.get("/api/v1/inventory", headers=headers)
    assert inv_res.status_code == 200
    data = inv_res.json()["data"]
    assert "items" in data
    assert "summary" in data

    # 2. Stock movements ledger for a product
    prod_id = env["non_ser_prod_id"]
    mov_res = client.get(f"/api/v1/inventory/{prod_id}/movements", headers=headers)
    assert mov_res.status_code == 200
    assert "items" in mov_res.json()["data"]

    # 3. Project shortages calculation
    if project_id:
        short_res = client.get(f"/api/v1/inventory/project-shortages/{project_id}", headers=headers)
        assert short_res.status_code == 200
        short_data = short_res.json()["data"]
        assert short_data["project_id"] == project_id
        assert "items" in short_data
        assert "shortage_items_count" in short_data


# ==========================================
# 7. ALL NINE CANONICAL ROLES RBAC VERIFICATION
# ==========================================

def test_all_nine_canonical_roles_security(setup_procurement_test_env):
    """
    Verify security matrix across all 9 canonical roles:
    - SUPER_ADMIN: Full read/write access.
    - WAREHOUSE_PROCUREMENT: Full read/write access.
    - DIRECTOR: Read oversight (suppliers, POs, inventory), write forbidden (403).
    - TECHNICAL_MANAGER: Read oversight (suppliers, POs, inventory), write forbidden (403).
    - FIELD_TECHNICIAN: Read serials (200), PO read forbidden (403), write forbidden (403).
    - SERVICE_WARRANTY: Read serials (200), PO read forbidden (403), write forbidden (403).
    - FINANCE_ACCOUNTS: PO write forbidden (403), PO read forbidden (403).
    - SALES: Procurement read and write forbidden (403).
    - CUSTOMER: Strictly forbidden across all procurement and inventory endpoints (403).
    """
    env = setup_procurement_test_env
    tokens = env["tokens"]
    prod_id = env["non_ser_prod_id"]

    write_payload = {
        "supplier_id": 1,
        "items": [{"product_id": prod_id, "ordered_quantity": 10, "unit_price": 50.00}],
    }

    # 1. SUPER_ADMIN: Allowed
    sa_h = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}
    assert client.get("/api/v1/purchase-orders", headers=sa_h).status_code == 200

    # 2. WAREHOUSE_PROCUREMENT: Allowed
    wp_h = {"Authorization": f"Bearer {tokens[SystemRole.WAREHOUSE_PROCUREMENT]}"}
    assert client.get("/api/v1/purchase-orders", headers=wp_h).status_code == 200

    # 3. DIRECTOR: Read allowed, write forbidden
    dir_h = {"Authorization": f"Bearer {tokens[SystemRole.DIRECTOR]}"}
    assert client.get("/api/v1/purchase-orders", headers=dir_h).status_code == 200
    assert client.get("/api/v1/inventory", headers=dir_h).status_code == 200
    assert client.post("/api/v1/purchase-orders", json=write_payload, headers=dir_h).status_code == 403

    # 4. TECHNICAL_MANAGER: Read allowed, write forbidden
    tm_h = {"Authorization": f"Bearer {tokens[SystemRole.TECHNICAL_MANAGER]}"}
    assert client.get("/api/v1/purchase-orders", headers=tm_h).status_code == 200
    assert client.post("/api/v1/purchase-orders", json=write_payload, headers=tm_h).status_code == 403

    # 5. FIELD_TECHNICIAN: Serials read allowed, PO read forbidden, write forbidden
    ft_h = {"Authorization": f"Bearer {tokens[SystemRole.FIELD_TECHNICIAN]}"}
    assert client.get(f"/api/v1/inventory/{prod_id}/serials", headers=ft_h).status_code == 200
    assert client.get("/api/v1/purchase-orders", headers=ft_h).status_code == 403
    assert client.post("/api/v1/purchase-orders", json=write_payload, headers=ft_h).status_code == 403

    # 6. SERVICE_WARRANTY: Serials read allowed, PO read forbidden, write forbidden
    sw_h = {"Authorization": f"Bearer {tokens[SystemRole.SERVICE_WARRANTY]}"}
    assert client.get(f"/api/v1/inventory/{prod_id}/serials", headers=sw_h).status_code == 200
    assert client.get("/api/v1/purchase-orders", headers=sw_h).status_code == 403
    assert client.post("/api/v1/purchase-orders", json=write_payload, headers=sw_h).status_code == 403

    # 7. FINANCE_ACCOUNTS: PO write forbidden, PO read forbidden
    fa_h = {"Authorization": f"Bearer {tokens[SystemRole.FINANCE_ACCOUNTS]}"}
    assert client.get("/api/v1/purchase-orders", headers=fa_h).status_code == 403
    assert client.post("/api/v1/purchase-orders", json=write_payload, headers=fa_h).status_code == 403

    # 8. SALES: Forbidden on read and write
    sales_h = {"Authorization": f"Bearer {tokens[SystemRole.SALES]}"}
    assert client.get("/api/v1/purchase-orders", headers=sales_h).status_code == 403
    assert client.post("/api/v1/purchase-orders", json=write_payload, headers=sales_h).status_code == 403

    # 9. CUSTOMER: Strictly forbidden
    cust_h = {"Authorization": f"Bearer {tokens[SystemRole.CUSTOMER]}"}
    assert client.get("/api/v1/purchase-orders", headers=cust_h).status_code == 403
    assert client.get("/api/v1/inventory", headers=cust_h).status_code == 403
    assert client.post("/api/v1/purchase-orders", json=write_payload, headers=cust_h).status_code == 403

