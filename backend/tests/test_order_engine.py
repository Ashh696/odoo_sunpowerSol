import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from decimal import Decimal
from datetime import date, timedelta
import uuid

from app.main import app
from app.database import SessionLocal
from app.models.auth import User, Role
from app.models.crm import Customer, Enquiry, Quotation, QuotationItem, Product
from app.models.projects import Order
from app.models.finance import Payment
from app.utils.roles import SystemRole
from app.utils.security import hash_password, create_access_token

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_order_test_env():
    tokens = {}
    user_ids = {}

    with SessionLocal() as db:
        role_slugs = [
            SystemRole.SUPER_ADMIN,
            SystemRole.DIRECTOR,
            SystemRole.SALES,
            SystemRole.TECHNICAL_MANAGER,
            SystemRole.FINANCE_ACCOUNTS,
            SystemRole.CUSTOMER,
        ]

        for slug in role_slugs:
            role_obj = db.execute(select(Role).where(Role.slug == slug)).scalar_one()
            email = f"test_{slug.lower()}_ord@sunpower.com"
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if not user:
                user = User(
                    role_id=role_obj.id,
                    email=email,
                    full_name=f"Test {slug} Ord",
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

        # Customer 2 for isolation testing
        cust_role = db.execute(select(Role).where(Role.slug == SystemRole.CUSTOMER)).scalar_one()
        email_cust2 = "test_customer2_ord@sunpower.com"
        cust2_user = db.execute(select(User).where(User.email == email_cust2)).scalar_one_or_none()
        if not cust2_user:
            cust2_user = User(
                role_id=cust_role.id,
                email=email_cust2,
                full_name="Second Customer Ord",
                hashed_password=hash_password("Pass123!Safe"),
                is_active=True,
                is_verified=True,
            )
            db.add(cust2_user)
            db.commit()
            db.refresh(cust2_user)

        tokens["CUSTOMER_2"] = create_access_token(
            data={"sub": str(cust2_user.id), "role": cust_role.slug, "email": cust2_user.email}
        )
        user_ids["CUSTOMER_2"] = cust2_user.id

        # Ensure Customer records exist in customers table
        cust1 = db.execute(select(Customer).where(Customer.user_id == user_ids[SystemRole.CUSTOMER])).scalar_one_or_none()
        if not cust1:
            cust1 = Customer(
                user_id=user_ids[SystemRole.CUSTOMER],
                full_name="Primary Test Customer",
                phone="9876543210",
                email="test_customer_ord@sunpower.com",
                address="100 Solar Street",
                city="Pune",
                state="Maharashtra",
                pincode="411001",
                created_by=user_ids[SystemRole.SUPER_ADMIN],
            )
            db.add(cust1)
            db.commit()
            db.refresh(cust1)

        cust2 = db.execute(select(Customer).where(Customer.user_id == user_ids["CUSTOMER_2"])).scalar_one_or_none()
        if not cust2:
            cust2 = Customer(
                user_id=user_ids["CUSTOMER_2"],
                full_name="Secondary Test Customer",
                phone="9876543211",
                email="test_customer2_ord@sunpower.com",
                address="200 Wind Way",
                city="Mumbai",
                state="Maharashtra",
                pincode="400001",
                created_by=user_ids[SystemRole.SUPER_ADMIN],
            )
            db.add(cust2)
            db.commit()
            db.refresh(cust2)

        # Ensure catalog product
        prod = db.execute(select(Product).where(Product.is_active == True)).first()
        if not prod:
            prod = Product(
                product_code=f"PANEL-{uuid.uuid4().hex[:6].upper()}",
                name="SunPower Monocrystalline 550W",
                category="SOLAR_PANEL",
                brand="SunPower",
                model_number="SP-550M",
                unit_of_measure="NOS",
                base_price=Decimal("15000.00"),
                tax_rate_percent=Decimal("12.00"),
                is_active=True,
            )
            db.add(prod)
            db.commit()
            db.refresh(prod)
        else:
            prod = prod[0]

        product_id = prod.id

    return tokens, user_ids, cust1.id, cust2.id, product_id


def _create_test_quotation(customer_id, user_id, status="ACCEPTED", net_payable=Decimal("200000.00")):
    with SessionLocal() as db:
        today = date.today()
        enq = Enquiry(
            enquiry_number=f"ENQ-{uuid.uuid4().hex[:6].upper()}",
            customer_id=customer_id,
            source="DIRECT",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("5.00"),
            monthly_electricity_bill=Decimal("5000.00"),
            status="WON" if status == "ACCEPTED" else "NEW",
        )
        db.add(enq)
        db.flush()

        prod = db.execute(select(Product).where(Product.is_active == True)).scalars().first()

        quo = Quotation(
            quotation_number=f"Q-ORD-{uuid.uuid4().hex[:6].upper()}",
            enquiry_id=enq.id,
            version=1,
            system_type="ON_GRID",
            capacity_kw=Decimal("5.00"),
            total_product_cost=net_payable,
            installation_cost=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            gross_amount=net_payable,
            subsidy_estimate=Decimal("0.00"),
            net_payable_amount=net_payable,
            valid_until=today + timedelta(days=30),
            quotation_date=today,
            status=status,
            created_by=user_id,
        )
        db.add(quo)
        db.flush()

        item = QuotationItem(
            quotation_id=quo.id,
            product_id=prod.id,
            item_description=prod.name,
            quantity=Decimal("10.00"),
            unit_price=Decimal("20000.00"),
            discount_amount=Decimal("0.00"),
            tax_rate_percent=Decimal("0.00"),
            total_amount=net_payable,
        )
        db.add(item)
        db.commit()
        db.refresh(quo)
        return quo.id


# ==========================================
# 1. ORDER CREATION TESTS
# ==========================================

def test_order_creation_from_accepted_quotation(setup_order_test_env):
    tokens, user_ids, cust1_id, _, _ = setup_order_test_env
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}

    quo_id = _create_test_quotation(cust1_id, user_ids[SystemRole.SUPER_ADMIN], status="ACCEPTED", net_payable=Decimal("185000.00"))

    # Convert to order
    payload = {"quotation_id": quo_id, "notes": "Customer accepted via WhatsApp confirmation"}
    res = client.post("/api/v1/orders", json=payload, headers=admin_headers)
    assert res.status_code == 201, res.text
    data = res.json()["data"]

    assert data["quotation_id"] == quo_id
    assert data["customer_id"] == cust1_id
    assert float(data["total_amount"]) == 185000.00
    assert float(data["advance_paid"]) == 0.00
    assert float(data["balance_amount"]) == 185000.00
    assert data["status"] == "PENDING_ADVANCE"
    assert data["order_number"].startswith("ORD-")
    assert data["customer"]["full_name"] == "Primary Test Customer"
    assert float(data["quotation"]["net_payable_amount"]) == 185000.00


def test_order_creation_rejected_for_non_accepted_quotation(setup_order_test_env):
    tokens, user_ids, cust1_id, _, _ = setup_order_test_env
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}

    for non_accepted_status in ["DRAFT", "PENDING_APPROVAL", "APPROVED", "SENT", "REJECTED"]:
        quo_id = _create_test_quotation(cust1_id, user_ids[SystemRole.SUPER_ADMIN], status=non_accepted_status)
        payload = {"quotation_id": quo_id}
        res = client.post("/api/v1/orders", json=payload, headers=admin_headers)
        assert res.status_code == 409, f"Expected 409 for status {non_accepted_status}, got {res.status_code}"
        assert "Only ACCEPTED quotations" in res.json()["detail"]


def test_duplicate_order_creation_rejected(setup_order_test_env):
    tokens, user_ids, cust1_id, _, _ = setup_order_test_env
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}

    quo_id = _create_test_quotation(cust1_id, user_ids[SystemRole.SUPER_ADMIN], status="ACCEPTED")

    # First conversion succeeds
    res1 = client.post("/api/v1/orders", json={"quotation_id": quo_id}, headers=admin_headers)
    assert res1.status_code == 201

    # Second conversion for same quotation must be rejected with 409
    res2 = client.post("/api/v1/orders", json={"quotation_id": quo_id}, headers=admin_headers)
    assert res2.status_code == 409
    assert "At most one order per quotation is permitted" in res2.json()["detail"]


def test_order_creation_unauthorized(setup_order_test_env):
    tokens, user_ids, cust1_id, _, _ = setup_order_test_env
    quo_id = _create_test_quotation(cust1_id, user_ids[SystemRole.SUPER_ADMIN], status="ACCEPTED")

    # Unauthorized roles without orders.create: SALES, CUSTOMER, TECHNICAL_MANAGER, FINANCE_ACCOUNTS
    unauthorized_roles = [SystemRole.SALES, SystemRole.CUSTOMER, SystemRole.TECHNICAL_MANAGER, SystemRole.FINANCE_ACCOUNTS]
    for role in unauthorized_roles:
        headers = {"Authorization": f"Bearer {tokens[role]}"}
        res = client.post("/api/v1/orders", json={"quotation_id": quo_id}, headers=headers)
        assert res.status_code == 403, f"Expected 403 for role {role}, got {res.status_code}"


# ==========================================
# 2. ORDER LIST, DETAIL & ISOLATION TESTS
# ==========================================

def test_order_list_filtering_and_pagination(setup_order_test_env):
    tokens, user_ids, cust1_id, _, _ = setup_order_test_env
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}

    quo_id = _create_test_quotation(cust1_id, user_ids[SystemRole.SUPER_ADMIN], status="ACCEPTED")
    res_create = client.post("/api/v1/orders", json={"quotation_id": quo_id}, headers=admin_headers)
    order_num = res_create.json()["data"]["order_number"]

    # Filter by search
    res_search = client.get(f"/api/v1/orders?search={order_num}", headers=admin_headers)
    assert res_search.status_code == 200
    assert len(res_search.json()["data"]["items"]) >= 1

    # Filter by customer
    res_cust = client.get(f"/api/v1/orders?customer_id={cust1_id}", headers=admin_headers)
    assert res_cust.status_code == 200
    for it in res_cust.json()["data"]["items"]:
        assert it["customer_id"] == cust1_id


def test_customer_order_isolation(setup_order_test_env):
    tokens, user_ids, cust1_id, cust2_id, _ = setup_order_test_env
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}
    cust1_headers = {"Authorization": f"Bearer {tokens[SystemRole.CUSTOMER]}"}
    cust2_headers = {"Authorization": f"Bearer {tokens['CUSTOMER_2']}"}

    # Create order for customer 1
    quo1_id = _create_test_quotation(cust1_id, user_ids[SystemRole.SUPER_ADMIN], status="ACCEPTED")
    res1 = client.post("/api/v1/orders", json={"quotation_id": quo1_id}, headers=admin_headers)
    order1_id = res1.json()["data"]["id"]

    # Customer 1 can retrieve own order
    res_c1 = client.get(f"/api/v1/orders/{order1_id}", headers=cust1_headers)
    assert res_c1.status_code == 200
    assert res_c1.json()["data"]["id"] == order1_id

    # Customer 2 attempting to view Customer 1's order is rejected with 403 Forbidden
    res_c2 = client.get(f"/api/v1/orders/{order1_id}", headers=cust2_headers)
    assert res_c2.status_code == 403
    assert "own customer account" in res_c2.json()["detail"]

    # Customer 2 listing orders sees none of Customer 1's orders
    res_list_c2 = client.get("/api/v1/orders", headers=cust2_headers)
    assert res_list_c2.status_code == 200
    for ord_item in res_list_c2.json()["data"]["items"]:
        assert ord_item["customer_id"] != cust1_id


# ==========================================
# 3. ORDER STATUS UPDATE & PAYMENT TESTS
# ==========================================

def test_order_status_update(setup_order_test_env):
    tokens, user_ids, cust1_id, _, _ = setup_order_test_env
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}

    quo_id = _create_test_quotation(cust1_id, user_ids[SystemRole.SUPER_ADMIN], status="ACCEPTED")
    res = client.post("/api/v1/orders", json={"quotation_id": quo_id}, headers=admin_headers)
    order_id = res.json()["data"]["id"]

    # Update to CONFIRMED
    res_up = client.put(f"/api/v1/orders/{order_id}/status", json={"status": "CONFIRMED", "notes": "Approved by management"}, headers=admin_headers)
    assert res_up.status_code == 200
    assert res_up.json()["data"]["status"] == "CONFIRMED"

    # Invalid status returns 400
    res_bad = client.put(f"/api/v1/orders/{order_id}/status", json={"status": "INVALID_STATE"}, headers=admin_headers)
    assert res_bad.status_code == 400


def test_order_payment_recording_and_financial_reconciliation(setup_order_test_env):
    tokens, user_ids, cust1_id, _, _ = setup_order_test_env
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}
    finance_headers = {"Authorization": f"Bearer {tokens[SystemRole.FINANCE_ACCOUNTS]}"}
    sales_headers = {"Authorization": f"Bearer {tokens[SystemRole.SALES]}"}

    quo_id = _create_test_quotation(cust1_id, user_ids[SystemRole.SUPER_ADMIN], status="ACCEPTED", net_payable=Decimal("100000.00"))
    res_ord = client.post("/api/v1/orders", json={"quotation_id": quo_id}, headers=admin_headers)
    order_id = res_ord.json()["data"]["id"]

    # 1. Non-finance user (SALES) cannot record payment
    res_unauth = client.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"amount": 25000.00, "payment_method": "UPI"},
        headers=sales_headers,
    )
    assert res_unauth.status_code == 403

    # 2. Overpayment (> balance) is rejected with 400
    res_over = client.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"amount": 150000.00, "payment_method": "NEFT"},
        headers=finance_headers,
    )
    assert res_over.status_code == 400
    assert "exceeds outstanding order balance" in res_over.json()["detail"]

    # 3. Valid advance payment recorded by FINANCE_ACCOUNTS
    ref = f"UPI-TXN-{uuid.uuid4().hex[:8].upper()}"
    res_pay = client.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"amount": 30000.00, "payment_method": "UPI", "transaction_reference": ref, "notes": "30% Advance Token"},
        headers=finance_headers,
    )
    assert res_pay.status_code == 201
    ord_data = res_pay.json()["data"]

    assert float(ord_data["advance_paid"]) == 30000.00
    assert float(ord_data["balance_amount"]) == 70000.00
    assert ord_data["status"] == "CONFIRMED"  # Automatically transitioned from PENDING_ADVANCE
    assert len(ord_data["payments"]) == 1
    assert ord_data["payments"][0]["transaction_reference"] == ref
