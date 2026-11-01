import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from decimal import Decimal
from datetime import date, timedelta
import uuid
from concurrent.futures import ThreadPoolExecutor

from app.main import app
from app.database import SessionLocal
from app.models.auth import User, Role
from app.models.crm import Customer, Enquiry, Quotation, QuotationItem, Product
from app.models.projects import Order, Project
from app.models.finance import Invoice, InvoiceItem, Payment, PaymentAllocation
from app.utils.roles import SystemRole
from app.utils.security import hash_password, create_access_token

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_finance_test_env():
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
            email = f"test_{slug.lower()}_fin@sunpower.com"
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if not user:
                user = User(
                    role_id=role_obj.id,
                    email=email,
                    full_name=f"Test {slug} Fin",
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
        email_cust2 = "test_customer2_fin@sunpower.com"
        cust2_user = db.execute(select(User).where(User.email == email_cust2)).scalar_one_or_none()
        if not cust2_user:
            cust2_user = User(
                role_id=cust_role.id,
                email=email_cust2,
                full_name="Second Customer Fin",
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

        # Customer 1 profile
        cust1 = db.execute(select(Customer).where(Customer.user_id == user_ids[SystemRole.CUSTOMER])).scalar_one_or_none()
        if not cust1:
            cust1 = Customer(
                user_id=user_ids[SystemRole.CUSTOMER],
                full_name="Primary Finance Customer",
                phone="9876543301",
                email="test_customer_fin@sunpower.com",
                address="700 Solar Blvd",
                city="Pune",
                state="Maharashtra",
                pincode="411001",
                created_by=user_ids[SystemRole.SUPER_ADMIN],
            )
            db.add(cust1)
            db.commit()
            db.refresh(cust1)

        # Customer 2 profile
        cust2 = db.execute(select(Customer).where(Customer.user_id == user_ids["CUSTOMER_2"])).scalar_one_or_none()
        if not cust2:
            cust2 = Customer(
                user_id=user_ids["CUSTOMER_2"],
                full_name="Secondary Finance Customer",
                phone="9876543302",
                email="test_customer2_fin@sunpower.com",
                address="800 Grid Lane",
                city="Mumbai",
                state="Maharashtra",
                pincode="400001",
                created_by=user_ids[SystemRole.SUPER_ADMIN],
            )
            db.add(cust2)
            db.commit()
            db.refresh(cust2)

        # Catalog product
        prod = db.execute(select(Product).where(Product.is_active == True)).scalars().first()
        if not prod:
            prod = Product(
                product_code=f"PANEL-FIN-{uuid.uuid4().hex[:6].upper()}",
                name="SunPower Monocrystalline 550W Module",
                category="SOLAR_PANEL",
                brand="SunPower",
                unit_of_measure="NOS",
                base_price=Decimal("15000.00"),
                tax_rate_percent=Decimal("12.00"),
                is_active=True,
            )
            db.add(prod)
            db.commit()
            db.refresh(prod)

        product_id = prod.id

    return tokens, user_ids, cust1.id, cust2.id, product_id


def _create_confirmed_test_order(customer_id, user_id, net_amount=Decimal("200000.00")):
    with SessionLocal() as db:
        today = date.today()
        enq = Enquiry(
            enquiry_number=f"ENQ-{uuid.uuid4().hex[:6].upper()}",
            customer_id=customer_id,
            source="DIRECT",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("5.00"),
            monthly_electricity_bill=Decimal("5000.00"),
            status="WON",
        )
        db.add(enq)
        db.flush()

        quo = Quotation(
            quotation_number=f"Q-FIN-{uuid.uuid4().hex[:6].upper()}",
            enquiry_id=enq.id,
            version=1,
            system_type="ON_GRID",
            capacity_kw=Decimal("5.00"),
            total_product_cost=net_amount,
            installation_cost=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            gross_amount=net_amount,
            subsidy_estimate=Decimal("0.00"),
            net_payable_amount=net_amount,
            valid_until=today + timedelta(days=30),
            quotation_date=today,
            status="ACCEPTED",
            created_by=user_id,
        )
        db.add(quo)
        db.flush()

        order = Order(
            order_number=f"ORD-FIN-{uuid.uuid4().hex[:6].upper()}",
            quotation_id=quo.id,
            customer_id=customer_id,
            order_date=today,
            total_amount=net_amount,
            advance_paid=Decimal("0.00"),
            balance_amount=net_amount,
            status="CONFIRMED",
            created_by=user_id,
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return order.id


# ==========================================
# 1. INVOICE CREATION TESTS
# ==========================================

def test_01_advance_invoice_creation(setup_finance_test_env):
    tokens, user_ids, cust1_id, _, prod_id = setup_finance_test_env
    fin_headers = {"Authorization": f"Bearer {tokens[SystemRole.FINANCE_ACCOUNTS]}"}
    order_id = _create_confirmed_test_order(cust1_id, user_ids[SystemRole.SUPER_ADMIN], net_amount=Decimal("150000.00"))

    payload = {
        "order_id": order_id,
        "invoice_type": "ADVANCE",
        "invoice_date": str(date.today()),
        "due_date": str(date.today() + timedelta(days=7)),
        "items": [
            {
                "product_id": prod_id,
                "item_description": "Initial 20% Booking Advance",
                "quantity": 1.0,
                "unit_price": 26785.71,
                "tax_rate_percent": 12.0,
            }
        ],
    }

    res = client.post("/api/v1/invoices", json=payload, headers=fin_headers)
    assert res.status_code == 201, res.text
    data = res.json()["data"]

    assert data["order_id"] == order_id
    assert data["customer_id"] == cust1_id
    assert data["invoice_type"] == "ADVANCE"
    assert data["invoice_number"].startswith("INV-")
    assert float(data["paid_amount"]) == 0.00
    assert float(data["balance_amount"]) == float(data["total_amount"])
    assert data["payment_status"] == "PENDING"
    assert len(data["items"]) == 1


def test_02_milestone_dispatch_and_installation_invoices(setup_finance_test_env):
    tokens, user_ids, cust1_id, _, prod_id = setup_finance_test_env
    fin_headers = {"Authorization": f"Bearer {tokens[SystemRole.FINANCE_ACCOUNTS]}"}
    order_id = _create_confirmed_test_order(cust1_id, user_ids[SystemRole.SUPER_ADMIN], net_amount=Decimal("200000.00"))

    # 1. Dispatch milestone invoice (50%)
    res_disp = client.post(
        "/api/v1/invoices",
        json={
            "order_id": order_id,
            "invoice_type": "MILESTONE_DISPATCH",
            "invoice_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=5)),
            "items": [{"product_id": prod_id, "quantity": 1.0, "unit_price": 89285.71, "tax_rate_percent": 12.0}],
        },
        headers=fin_headers,
    )
    assert res_disp.status_code == 201

    # 2. Installation milestone invoice (30%)
    res_inst = client.post(
        "/api/v1/invoices",
        json={
            "order_id": order_id,
            "invoice_type": "MILESTONE_INSTALLATION",
            "invoice_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=5)),
            "items": [{"product_id": prod_id, "quantity": 1.0, "unit_price": 53571.43, "tax_rate_percent": 12.0}],
        },
        headers=fin_headers,
    )
    assert res_inst.status_code == 201


def test_03_duplicate_milestone_type_rejected(setup_finance_test_env):
    tokens, user_ids, cust1_id, _, prod_id = setup_finance_test_env
    fin_headers = {"Authorization": f"Bearer {tokens[SystemRole.FINANCE_ACCOUNTS]}"}
    order_id = _create_confirmed_test_order(cust1_id, user_ids[SystemRole.SUPER_ADMIN], net_amount=Decimal("100000.00"))

    payload = {
        "order_id": order_id,
        "invoice_type": "ADVANCE",
        "invoice_date": str(date.today()),
        "due_date": str(date.today() + timedelta(days=7)),
        "items": [{"product_id": prod_id, "quantity": 1.0, "unit_price": 20000.0, "tax_rate_percent": 0.0}],
    }

    res1 = client.post("/api/v1/invoices", json=payload, headers=fin_headers)
    assert res1.status_code == 201

    # Second ADVANCE invoice on same order must be rejected with 409 Conflict
    res2 = client.post("/api/v1/invoices", json=payload, headers=fin_headers)
    assert res2.status_code == 409
    assert "Duplicate milestone billing is rejected" in res2.json()["detail"]


def test_04_invoice_exceeding_order_limit_rejected(setup_finance_test_env):
    tokens, user_ids, cust1_id, _, prod_id = setup_finance_test_env
    fin_headers = {"Authorization": f"Bearer {tokens[SystemRole.FINANCE_ACCOUNTS]}"}
    order_id = _create_confirmed_test_order(cust1_id, user_ids[SystemRole.SUPER_ADMIN], net_amount=Decimal("50000.00"))

    # Invoice for 75,000 against a 50,000 order must fail with 400
    payload = {
        "order_id": order_id,
        "invoice_type": "ADVANCE",
        "invoice_date": str(date.today()),
        "due_date": str(date.today() + timedelta(days=7)),
        "items": [{"product_id": prod_id, "quantity": 1.0, "unit_price": 75000.0, "tax_rate_percent": 0.0}],
    }

    res = client.post("/api/v1/invoices", json=payload, headers=fin_headers)
    assert res.status_code == 400
    assert "exceeds remaining billable order limit" in res.json()["detail"]


def test_05_invalid_dates_and_line_items_rejected(setup_finance_test_env):
    tokens, user_ids, cust1_id, _, prod_id = setup_finance_test_env
    fin_headers = {"Authorization": f"Bearer {tokens[SystemRole.FINANCE_ACCOUNTS]}"}
    order_id = _create_confirmed_test_order(cust1_id, user_ids[SystemRole.SUPER_ADMIN], net_amount=Decimal("100000.00"))

    # 1. due_date < invoice_date
    res_date = client.post(
        "/api/v1/invoices",
        json={
            "order_id": order_id,
            "invoice_type": "ADVANCE",
            "invoice_date": str(date.today()),
            "due_date": str(date.today() - timedelta(days=1)),
            "items": [{"product_id": prod_id, "quantity": 1.0, "unit_price": 10000.0, "tax_rate_percent": 0.0}],
        },
        headers=fin_headers,
    )
    assert res_date.status_code == 400
    assert "cannot be earlier than invoice date" in res_date.json()["detail"]

    # 2. quantity <= 0
    res_qty = client.post(
        "/api/v1/invoices",
        json={
            "order_id": order_id,
            "invoice_type": "ADVANCE",
            "invoice_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=7)),
            "items": [{"product_id": prod_id, "quantity": 0.0, "unit_price": 10000.0, "tax_rate_percent": 0.0}],
        },
        headers=fin_headers,
    )
    assert res_qty.status_code == 422  # Pydantic validation (gt=0)


# ==========================================
# 2. PAYMENT ALLOCATION TESTS
# ==========================================

def test_06_payment_allocation_full_and_partial(setup_finance_test_env):
    tokens, user_ids, cust1_id, _, prod_id = setup_finance_test_env
    fin_headers = {"Authorization": f"Bearer {tokens[SystemRole.FINANCE_ACCOUNTS]}"}
    order_id = _create_confirmed_test_order(cust1_id, user_ids[SystemRole.SUPER_ADMIN], net_amount=Decimal("100000.00"))

    # Create Invoice of 50,000
    res_inv = client.post(
        "/api/v1/invoices",
        json={
            "order_id": order_id,
            "invoice_type": "ADVANCE",
            "invoice_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=7)),
            "items": [{"product_id": prod_id, "quantity": 1.0, "unit_price": 50000.0, "tax_rate_percent": 0.0}],
        },
        headers=fin_headers,
    )
    inv_id = res_inv.json()["data"]["id"]

    # Record Payment of 50,000 on order
    res_pay = client.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"amount": 50000.00, "payment_method": "NEFT", "transaction_reference": f"NEFT-{uuid.uuid4().hex[:6].upper()}"},
        headers=fin_headers,
    )
    pay_id = res_pay.json()["data"]["payments"][-1]["id"]

    # 1. Partial allocation of 20,000
    res_alloc1 = client.post(
        f"/api/v1/invoices/{inv_id}/allocations",
        json={"payment_id": pay_id, "allocated_amount": 20000.00},
        headers=fin_headers,
    )
    assert res_alloc1.status_code == 201
    data1 = res_alloc1.json()["data"]
    assert float(data1["paid_amount"]) == 20000.00
    assert float(data1["balance_amount"]) == 30000.00
    assert data1["payment_status"] == "PARTIALLY_PAID"

    # 2. Second allocation of remaining 30,000 -> full payment
    res_alloc2 = client.post(
        f"/api/v1/invoices/{inv_id}/allocations",
        json={"payment_id": pay_id, "allocated_amount": 30000.00},
        headers=fin_headers,
    )
    assert res_alloc2.status_code == 201
    data2 = res_alloc2.json()["data"]
    assert float(data2["paid_amount"]) == 50000.00
    assert float(data2["balance_amount"]) == 0.00
    assert data2["payment_status"] == "PAID"


def test_07_payment_over_allocation_and_insufficient_funds_rejected(setup_finance_test_env):
    tokens, user_ids, cust1_id, _, prod_id = setup_finance_test_env
    fin_headers = {"Authorization": f"Bearer {tokens[SystemRole.FINANCE_ACCOUNTS]}"}
    order_id = _create_confirmed_test_order(cust1_id, user_ids[SystemRole.SUPER_ADMIN], net_amount=Decimal("100000.00"))

    # Invoice for 30,000
    res_inv = client.post(
        "/api/v1/invoices",
        json={
            "order_id": order_id,
            "invoice_type": "ADVANCE",
            "invoice_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=7)),
            "items": [{"product_id": prod_id, "quantity": 1.0, "unit_price": 30000.0, "tax_rate_percent": 0.0}],
        },
        headers=fin_headers,
    )
    inv_id = res_inv.json()["data"]["id"]

    # Payment of 20,000
    res_pay = client.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"amount": 20000.00, "payment_method": "UPI", "transaction_reference": f"UPI-{uuid.uuid4().hex[:6].upper()}"},
        headers=fin_headers,
    )
    pay_id = res_pay.json()["data"]["payments"][-1]["id"]

    # Allocating 25,000 (exceeds payment of 20,000) must return 400
    res_over = client.post(
        f"/api/v1/invoices/{inv_id}/allocations",
        json={"payment_id": pay_id, "allocated_amount": 25000.00},
        headers=fin_headers,
    )
    assert res_over.status_code == 400
    assert "exceeds available payment balance" in res_over.json()["detail"]


def test_08_cross_order_or_customer_mismatch_rejected(setup_finance_test_env):
    tokens, user_ids, cust1_id, cust2_id, prod_id = setup_finance_test_env
    fin_headers = {"Authorization": f"Bearer {tokens[SystemRole.FINANCE_ACCOUNTS]}"}

    # Order 1 (Cust 1)
    ord1_id = _create_confirmed_test_order(cust1_id, user_ids[SystemRole.SUPER_ADMIN], net_amount=Decimal("50000.00"))
    res_inv1 = client.post(
        "/api/v1/invoices",
        json={
            "order_id": ord1_id,
            "invoice_type": "ADVANCE",
            "invoice_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=7)),
            "items": [{"product_id": prod_id, "quantity": 1.0, "unit_price": 20000.0, "tax_rate_percent": 0.0}],
        },
        headers=fin_headers,
    )
    inv1_id = res_inv1.json()["data"]["id"]

    # Order 2 (Cust 2)
    ord2_id = _create_confirmed_test_order(cust2_id, user_ids[SystemRole.SUPER_ADMIN], net_amount=Decimal("50000.00"))
    res_pay2 = client.post(
        f"/api/v1/orders/{ord2_id}/payments",
        json={"amount": 20000.00, "payment_method": "UPI", "transaction_reference": f"UPI-{uuid.uuid4().hex[:6].upper()}"},
        headers=fin_headers,
    )
    pay2_id = res_pay2.json()["data"]["payments"][-1]["id"]

    # Attempting to allocate Cust 2's payment to Cust 1's invoice must fail with 400
    res_cross = client.post(
        f"/api/v1/invoices/{inv1_id}/allocations",
        json={"payment_id": pay2_id, "allocated_amount": 10000.00},
        headers=fin_headers,
    )
    assert res_cross.status_code == 400
    assert "belongs to order" in res_cross.json()["detail"]


# ==========================================
# 3. DIRECT INVOICE PAYMENT TESTS
# ==========================================

def test_09_direct_invoice_payment_atomic(setup_finance_test_env):
    tokens, user_ids, cust1_id, _, prod_id = setup_finance_test_env
    fin_headers = {"Authorization": f"Bearer {tokens[SystemRole.FINANCE_ACCOUNTS]}"}
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}
    order_id = _create_confirmed_test_order(cust1_id, user_ids[SystemRole.SUPER_ADMIN], net_amount=Decimal("120000.00"))

    res_inv = client.post(
        "/api/v1/invoices",
        json={
            "order_id": order_id,
            "invoice_type": "ADVANCE",
            "invoice_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=7)),
            "items": [{"product_id": prod_id, "quantity": 1.0, "unit_price": 40000.0, "tax_rate_percent": 0.0}],
        },
        headers=fin_headers,
    )
    inv_id = res_inv.json()["data"]["id"]

    # Direct invoice payment of 40,000
    ref = f"DIR-UPI-{uuid.uuid4().hex[:6].upper()}"
    res_pay = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"amount": 40000.00, "payment_method": "UPI", "transaction_reference": ref, "notes": "Online direct gateway pay"},
        headers=fin_headers,
    )
    assert res_pay.status_code == 201
    data = res_pay.json()["data"]

    # Invoice fully paid
    assert float(data["paid_amount"]) == 40000.00
    assert float(data["balance_amount"]) == 0.00
    assert data["payment_status"] == "PAID"
    assert len(data["allocations"]) == 1

    # Verify Order balances updated atomically
    res_ord = client.get(f"/api/v1/orders/{order_id}", headers=admin_headers)
    ord_data = res_ord.json()["data"]
    assert float(ord_data["advance_paid"]) == 40000.00
    assert float(ord_data["balance_amount"]) == 80000.00


# ==========================================
# 4. CUSTOMER ISOLATION & RBAC TESTS
# ==========================================

def test_10_customer_invoice_and_payment_isolation(setup_finance_test_env):
    tokens, user_ids, cust1_id, cust2_id, prod_id = setup_finance_test_env
    fin_headers = {"Authorization": f"Bearer {tokens[SystemRole.FINANCE_ACCOUNTS]}"}
    cust1_headers = {"Authorization": f"Bearer {tokens[SystemRole.CUSTOMER]}"}
    cust2_headers = {"Authorization": f"Bearer {tokens['CUSTOMER_2']}"}

    ord1_id = _create_confirmed_test_order(cust1_id, user_ids[SystemRole.SUPER_ADMIN], net_amount=Decimal("60000.00"))
    res_inv1 = client.post(
        "/api/v1/invoices",
        json={
            "order_id": ord1_id,
            "invoice_type": "ADVANCE",
            "invoice_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=7)),
            "items": [{"product_id": prod_id, "quantity": 1.0, "unit_price": 30000.0, "tax_rate_percent": 0.0}],
        },
        headers=fin_headers,
    )
    inv1_id = res_inv1.json()["data"]["id"]

    # Customer 1 can view own invoice
    res_c1 = client.get(f"/api/v1/invoices/{inv1_id}", headers=cust1_headers)
    assert res_c1.status_code == 200
    assert res_c1.json()["data"]["id"] == inv1_id

    # Customer 2 attempting to view Customer 1's invoice gets 403 Forbidden
    res_c2 = client.get(f"/api/v1/invoices/{inv1_id}", headers=cust2_headers)
    assert res_c2.status_code == 403
    assert "belonging to your own customer account" in res_c2.json()["detail"]

    # Customer 2 invoice list displays none of Customer 1's invoices
    res_list_c2 = client.get("/api/v1/invoices", headers=cust2_headers)
    assert res_list_c2.status_code == 200
    for item in res_list_c2.json()["data"]["items"]:
        assert item["customer_id"] != cust1_id


def test_11_rbac_unauthorized_actions(setup_finance_test_env):
    tokens, user_ids, cust1_id, _, prod_id = setup_finance_test_env
    sales_headers = {"Authorization": f"Bearer {tokens[SystemRole.SALES]}"}
    order_id = _create_confirmed_test_order(cust1_id, user_ids[SystemRole.SUPER_ADMIN], net_amount=Decimal("50000.00"))

    # SALES role has no invoices.create -> 403
    res_create = client.post(
        "/api/v1/invoices",
        json={
            "order_id": order_id,
            "invoice_type": "ADVANCE",
            "invoice_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=7)),
            "items": [{"product_id": prod_id, "quantity": 1.0, "unit_price": 10000.0, "tax_rate_percent": 0.0}],
        },
        headers=sales_headers,
    )
    assert res_create.status_code == 403

    # SALES role has no payments.record -> 403
    res_alloc = client.post(
        "/api/v1/invoices/999/allocations",
        json={"payment_id": 1, "allocated_amount": 5000.0},
        headers=sales_headers,
    )
    assert res_alloc.status_code == 403


# ==========================================
# 5. MULTI-THREADED CONCURRENCY TEST
# ==========================================

def test_12_concurrent_allocations_prevent_overspend(setup_finance_test_env):
    """
    Test genuinely concurrent allocation requests via ThreadPoolExecutor against the same payment.
    Ensures that with_for_update row locking and balance checks serialize allocations,
    preventing overspending of the payment's unallocated amount.
    """
    tokens, user_ids, cust1_id, _, prod_id = setup_finance_test_env
    fin_headers = {"Authorization": f"Bearer {tokens[SystemRole.FINANCE_ACCOUNTS]}"}
    order_id = _create_confirmed_test_order(cust1_id, user_ids[SystemRole.SUPER_ADMIN], net_amount=Decimal("150000.00"))

    # Create Invoice of 100,000
    res_inv = client.post(
        "/api/v1/invoices",
        json={
            "order_id": order_id,
            "invoice_type": "ADVANCE",
            "invoice_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=7)),
            "items": [{"product_id": prod_id, "quantity": 1.0, "unit_price": 100000.0, "tax_rate_percent": 0.0}],
        },
        headers=fin_headers,
    )
    inv_id = res_inv.json()["data"]["id"]

    # Record Payment of 50,000
    res_pay = client.post(
        f"/api/v1/orders/{order_id}/payments",
        json={"amount": 50000.00, "payment_method": "NEFT", "transaction_reference": f"CONC-NEFT-{uuid.uuid4().hex[:6].upper()}"},
        headers=fin_headers,
    )
    pay_id = res_pay.json()["data"]["payments"][-1]["id"]

    # Launch 3 simultaneous requests to allocate 30,000 each (Total requested: 90,000, Available: 50,000)
    def attempt_allocation(amt):
        # Dedicated client call in worker thread
        return client.post(
            f"/api/v1/invoices/{inv_id}/allocations",
            json={"payment_id": pay_id, "allocated_amount": amt},
            headers=fin_headers,
        )

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(attempt_allocation, 30000.00) for _ in range(3)]
        responses = [f.result() for f in futures]

    statuses = [r.status_code for r in responses]
    successes = [s for s in statuses if s == 201]
    rejections = [s for s in statuses if s == 400]

    # Exactly ONE allocation of 30,000 can succeed (remaining balance 20,000 cannot satisfy another 30,000 request)
    assert len(successes) == 1, f"Expected exactly 1 successful allocation, got {statuses}"
    assert len(rejections) == 2, f"Expected 2 rejections, got {statuses}"

    # Verify database state integrity
    with SessionLocal() as db:
        payment = db.execute(select(Payment).where(Payment.id == pay_id)).scalar_one()
        invoice = db.execute(select(Invoice).where(Invoice.id == inv_id)).scalar_one()

        assert float(payment.unallocated_amount) == 20000.00
        assert float(invoice.paid_amount) == 30000.00
        assert float(invoice.balance_amount) == 70000.00
