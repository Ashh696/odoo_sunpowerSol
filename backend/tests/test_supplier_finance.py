import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from decimal import Decimal
from datetime import date, timedelta
import uuid

from app.main import app
from app.database import SessionLocal
from app.models.auth import User, Role
from app.models.crm import Customer, Product, Enquiry, Quotation
from app.models.projects import (
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
    SupplierInvoice,
    SupplierPayment,
    SupplierPaymentAllocation,
    Order,
    Project,
    ProjectBomItem,
)
from app.models.finance import ProjectCost, Invoice
from app.utils.roles import SystemRole
from app.utils.security import hash_password, create_access_token

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_finance_env():
    tokens = {}
    user_ids = {}

    with SessionLocal() as db:
        role_slugs = [
            SystemRole.SUPER_ADMIN,
            SystemRole.DIRECTOR,
            SystemRole.FINANCE_ACCOUNTS,
            SystemRole.WAREHOUSE_PROCUREMENT,
            SystemRole.SALES,
            SystemRole.FIELD_TECHNICIAN,
        ]
        for slug in role_slugs:
            role = db.execute(select(Role).where(Role.slug == slug)).scalar_one_or_none()
            if not role:
                role = Role(name=slug.replace("_", " ").title(), slug=slug)
                db.add(role)
                db.flush()

            test_email = f"test_{slug.lower()}@sunpowersol.test"
            user = db.execute(select(User).where(User.email == test_email)).scalar_one_or_none()
            if not user:
                user = User(
                    email=test_email,
                    hashed_password=hash_password("TestSecret123!"),
                    full_name=f"Test {slug}",
                    role_id=role.id,
                    is_active=True,
                )
                db.add(user)
                db.flush()

            tokens[slug] = create_access_token(data={"sub": str(user.id), "role": slug, "email": user.email})
            user_ids[slug] = user.id

        # Create Supplier
        uid = uuid.uuid4().hex[:6]
        supplier = Supplier(
            supplier_code=f"SUP-AP-{uid.upper()}",
            company_name=f"AP Apex Inverters {uid}",
            contact_person="Ramesh Patel",
            email=f"ap_{uid}@apexinverters.test",
            phone=f"98{uid[:8]}",
            address="123 Industrial Area Phase 2",
            city="Pune",
            state="Maharashtra",
            gst_number=f"27AAAPA{uid[:4].upper()}1Z5",
            pan_number=f"AAAPA{uid[:4].upper()}Z",
            is_active=True,
        )
        db.add(supplier)
        db.flush()

        # Create Product
        product = Product(
            product_code=f"INV-10K-{uid.upper()}",
            name=f"Solar Hybrid Inverter 10kW {uid}",
            category="INVERTER",
            unit_of_measure="NOS",
            brand="Growatt",
            model_number="SPH10000",
            wattage_or_capacity="10000W",
            base_price=Decimal("120000.00"),
            tax_rate_percent=Decimal("12.00"),
            min_stock_alert=Decimal("2.00"),
            is_serialized=True,
            is_active=True,
        )
        db.add(product)
        db.flush()

        # Create Purchase Order
        po = PurchaseOrder(
            po_number=f"PO-AP-{uid.upper()}",
            supplier_id=supplier.id,
            status="ISSUED",
            po_date=date.today(),
            expected_delivery_date=date.today() + timedelta(days=14),
            total_amount=Decimal("134400.00"),
            tax_amount=Decimal("14400.00"),
            created_by=user_ids[SystemRole.WAREHOUSE_PROCUREMENT],
        )
        db.add(po)
        db.flush()

        po_item = PurchaseOrderItem(
            purchase_order_id=po.id,
            product_id=product.id,
            ordered_quantity=Decimal("1.00"),
            received_quantity=Decimal("1.00"),
            unit_price=Decimal("120000.00"),
            tax_rate_percent=Decimal("12.00"),
            total_amount=Decimal("134400.00"),
        )
        db.add(po_item)
        db.flush()

        # Create Customer, Enquiry, Quotation, Order, Project
        cust = Customer(
            full_name=f"Finance Test Client {uid}",
            customer_type="INDIVIDUAL",
            phone=f"99{uid[:8]}",
            email=f"client_{uid}@test.com",
            address="45 Industrial Park, Pune",
            city="Pune",
            state="Maharashtra",
            pincode="411001",
            created_by=user_ids[SystemRole.SALES],
            is_active=True,
        )
        db.add(cust)
        db.flush()

        enquiry = Enquiry(
            enquiry_number=f"ENQ-AP-{uid.upper()}",
            customer_id=cust.id,
            source="WEBSITE",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("10.00"),
            status="WON",
        )
        db.add(enquiry)
        db.flush()

        quotation = Quotation(
            quotation_number=f"QT-AP-{uid.upper()}",
            enquiry_id=enquiry.id,
            version=1,
            system_type="ON_GRID",
            capacity_kw=Decimal("10.00"),
            total_product_cost=Decimal("220000.00"),
            installation_cost=Decimal("0.00"),
            tax_amount=Decimal("30000.00"),
            gross_amount=Decimal("250000.00"),
            subsidy_estimate=Decimal("0.00"),
            net_payable_amount=Decimal("250000.00"),
            valid_until=date.today() + timedelta(days=30),
            quotation_date=date.today(),
            status="ACCEPTED",
            created_by=user_ids[SystemRole.SALES],
        )
        db.add(quotation)
        db.flush()

        order = Order(
            quotation_id=quotation.id,
            customer_id=cust.id,
            order_number=f"ORD-AP-{uid.upper()}",
            order_date=date.today(),
            status="CONFIRMED",
            total_amount=Decimal("250000.00"),
            advance_paid=Decimal("50000.00"),
            balance_amount=Decimal("200000.00"),
            created_by=user_ids[SystemRole.SALES],
        )
        db.add(order)
        db.flush()

        project = Project(
            order_id=order.id,
            customer_id=cust.id,
            project_code=f"PRJ-AP-{uid.upper()}",
            system_capacity_kw=Decimal("10.00"),
            system_type="ON_GRID",
            site_address="45 Industrial Park, Pune",
            planned_start_date=date.today(),
            planned_completion_date=date.today() + timedelta(days=30),
            status="INSTALLATION",
        )
        db.add(project)
        db.flush()

        bom_item = ProjectBomItem(
            project_id=project.id,
            product_id=product.id,
            item_category="INVERTER",
            planned_quantity=Decimal("1.00"),
            allocated_quantity=Decimal("1.00"),
            dispatched_quantity=Decimal("1.00"),
            installed_quantity=Decimal("1.00"),
            unit_cost_snapshot=Decimal("120000.00"),
        )
        db.add(bom_item)

        # Customer invoice for revenue collection tracking
        inv = Invoice(
            invoice_number=f"INV-CUST-{uid.upper()}",
            order_id=order.id,
            project_id=project.id,
            customer_id=cust.id,
            invoice_type="FINAL",
            invoice_date=date.today(),
            due_date=date.today() + timedelta(days=15),
            subtotal=Decimal("220000.00"),
            tax_amount=Decimal("30000.00"),
            total_amount=Decimal("250000.00"),
            paid_amount=Decimal("100000.00"),
            balance_amount=Decimal("150000.00"),
            payment_status="PARTIALLY_PAID",
        )
        db.add(inv)

        db.commit()

        env_data = {
            "supplier_id": supplier.id,
            "po_id": po.id,
            "po_total": Decimal("134400.00"),
            "product_id": product.id,
            "order_id": order.id,
            "project_id": project.id,
            "tokens": tokens,
            "uid": uid,
        }

    return env_data


def test_supplier_invoice_creation_and_variance(setup_finance_env):
    data = setup_finance_env
    fin_token = data["tokens"][SystemRole.FINANCE_ACCOUNTS]
    po_id = data["po_id"]
    uid = data["uid"]

    headers = {"Authorization": f"Bearer {fin_token}"}
    invoice_payload = {
        "purchase_order_id": po_id,
        "invoice_number": f"SINV-{uid}-001",
        "invoice_date": str(date.today()),
        "subtotal": "125000.00",
        "tax_amount": "15000.00",
        "total_amount": "140000.00",  # PO was 134400, variance should be +5600.00
    }

    resp = client.post("/api/v1/supplier-invoices", json=invoice_payload, headers=headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()["data"]

    assert body["invoice_number"] == f"SINV-{uid}-001"
    assert float(body["total_amount"]) == 140000.00
    assert float(body["balance_amount"]) == 140000.00
    assert float(body["paid_amount"]) == 0.00
    assert body["payment_status"] == "PENDING"
    assert float(body["variance_amount"]) == 5600.00

    # Test duplicate invoice rejection
    dup_resp = client.post("/api/v1/supplier-invoices", json=invoice_payload, headers=headers)
    assert dup_resp.status_code == 400
    assert "already been recorded" in dup_resp.json()["detail"].lower()


def test_direct_supplier_invoice_payment(setup_finance_env):
    data = setup_finance_env
    fin_token = data["tokens"][SystemRole.FINANCE_ACCOUNTS]
    po_id = data["po_id"]
    uid = data["uid"]
    headers = {"Authorization": f"Bearer {fin_token}"}

    # Create another invoice for direct payment test
    inv_payload = {
        "purchase_order_id": po_id,
        "invoice_number": f"SINV-{uid}-DIRECT",
        "subtotal": "50000.00",
        "tax_amount": "6000.00",
        "total_amount": "56000.00",
    }
    c_resp = client.post("/api/v1/supplier-invoices", json=inv_payload, headers=headers)
    assert c_resp.status_code == 201
    inv_id = c_resp.json()["data"]["id"]

    # Direct payment of 30,000 (Partial)
    pay_payload = {
        "amount": "30000.00",
        "payment_mode": "NEFT",
        "payment_reference": f"UTR-{uid}-D1",
        "notes": "Advance direct settlement",
    }
    pay_resp = client.post(f"/api/v1/supplier-invoices/{inv_id}/payments", json=pay_payload, headers=headers)
    assert pay_resp.status_code == 201, pay_resp.text
    inv_data = pay_resp.json()["data"]

    assert float(inv_data["paid_amount"]) == 30000.00
    assert float(inv_data["balance_amount"]) == 26000.00
    assert inv_data["payment_status"] == "PARTIALLY_PAID"
    assert len(inv_data["allocations"]) == 1
    assert float(inv_data["allocations"][0]["allocated_amount"]) == 30000.00

    # Overpayment rejection
    overpay = {"amount": "27000.00"}
    bad_resp = client.post(f"/api/v1/supplier-invoices/{inv_id}/payments", json=overpay, headers=headers)
    assert bad_resp.status_code == 400
    assert "exceeds" in bad_resp.json()["detail"].lower()

    # Complete payment
    final_pay = {"amount": "26000.00", "payment_mode": "RTGS"}
    fin_pay_resp = client.post(f"/api/v1/supplier-invoices/{inv_id}/payments", json=final_pay, headers=headers)
    assert fin_pay_resp.status_code == 201
    final_inv = fin_pay_resp.json()["data"]
    assert float(final_inv["paid_amount"]) == 56000.00
    assert float(final_inv["balance_amount"]) == 0.00
    assert final_inv["payment_status"] == "PAID"
    assert len(final_inv["allocations"]) == 2


def test_supplier_payment_and_allocation(setup_finance_env):
    data = setup_finance_env
    fin_token = data["tokens"][SystemRole.FINANCE_ACCOUNTS]
    supplier_id = data["supplier_id"]
    po_id = data["po_id"]
    uid = data["uid"]
    headers = {"Authorization": f"Bearer {fin_token}"}

    # 1. Record standalone supplier payment of 100,000
    spay_payload = {
        "supplier_id": supplier_id,
        "amount": "100000.00",
        "payment_mode": "BANK_TRANSFER",
        "payment_reference": f"SPAY-REF-{uid}",
        "notes": "Bulk supplier on-account advance",
    }
    p_resp = client.post("/api/v1/supplier-payments", json=spay_payload, headers=headers)
    assert p_resp.status_code == 201, p_resp.text
    spay_data = p_resp.json()["data"]
    spay_id = spay_data["id"]
    assert float(spay_data["amount"]) == 100000.00
    assert float(spay_data["unallocated_amount"]) == 100000.00

    # 2. Record new invoice for 60,000
    inv_payload = {
        "purchase_order_id": po_id,
        "invoice_number": f"SINV-{uid}-ALLOC",
        "subtotal": "55000.00",
        "tax_amount": "5000.00",
        "total_amount": "60000.00",
    }
    inv_resp = client.post("/api/v1/supplier-invoices", json=inv_payload, headers=headers)
    assert inv_resp.status_code == 201
    inv_id = inv_resp.json()["data"]["id"]

    # 3. Attempt allocation greater than invoice balance (e.g. 70,000)
    bad_alloc = {
        "supplier_payment_id": spay_id,
        "allocated_amount": "70000.00",
    }
    fail_resp = client.post(f"/api/v1/supplier-invoices/{inv_id}/allocations", json=bad_alloc, headers=headers)
    assert fail_resp.status_code == 400
    assert "exceeds" in fail_resp.json()["detail"].lower()

    # 4. Allocate 40,000
    alloc_payload = {
        "supplier_payment_id": spay_id,
        "allocated_amount": "40000.00",
    }
    ok_resp = client.post(f"/api/v1/supplier-invoices/{inv_id}/allocations", json=alloc_payload, headers=headers)
    assert ok_resp.status_code == 201, ok_resp.text
    updated_inv = ok_resp.json()["data"]
    assert float(updated_inv["paid_amount"]) == 40000.00
    assert float(updated_inv["balance_amount"]) == 20000.00
    assert updated_inv["payment_status"] == "PARTIALLY_PAID"

    # 5. Check payment remaining unallocated amount via DB
    with SessionLocal() as db:
        sp = db.get(SupplierPayment, spay_id)
        assert float(sp.unallocated_amount) == 60000.00


def test_project_costs_and_profitability(setup_finance_env):
    data = setup_finance_env
    fin_token = data["tokens"][SystemRole.FINANCE_ACCOUNTS]
    project_id = data["project_id"]
    headers = {"Authorization": f"Bearer {fin_token}"}

    # 1. Record Labor and Transport direct costs
    cost_labor = {
        "cost_category": "LABOR",
        "cost_amount": "15000.00",
        "source_reference_type": "CONTRACTOR_WAGES",
    }
    c1 = client.post(f"/api/v1/projects/{project_id}/costs", json=cost_labor, headers=headers)
    assert c1.status_code == 201, c1.text
    assert float(c1.json()["data"]["cost_amount"]) == 15000.00

    cost_trans = {
        "cost_category": "TRANSPORT",
        "cost_amount": "5000.00",
        "source_reference_type": "LOGISTICS_FREIGHT",
    }
    c2 = client.post(f"/api/v1/projects/{project_id}/costs", json=cost_trans, headers=headers)
    assert c2.status_code == 201, c2.text

    # 2. Query Project Profitability
    # Order contract: 250,000
    # Customer collected: 100,000
    # Material cost from BOM: 1 unit * 120,000 = 120,000
    # Labor: 15,000
    # Transport/Other: 5,000
    # Total incurred: 140,000
    # Gross profit: 250,000 - 140,000 = 110,000
    # Gross margin %: (110,000 / 250,000) * 100 = 44.00%
    prof_resp = client.get(f"/api/v1/projects/{project_id}/profitability", headers=headers)
    assert prof_resp.status_code == 200, prof_resp.text
    prof = prof_resp.json()["data"]

    assert float(prof["contract_amount"]) == 250000.00
    assert float(prof["total_collected"]) == 100000.00
    assert float(prof["material_cost"]) == 120000.00
    assert float(prof["labor_installation_cost"]) == 15000.00
    assert float(prof["other_direct_costs"]) == 5000.00
    assert float(prof["total_incurred_cost"]) == 140000.00
    assert float(prof["gross_profit"]) == 110000.00
    assert float(prof["gross_margin_percentage"]) == 44.00


def test_finance_rbac_restrictions(setup_finance_env):
    data = setup_finance_env
    sales_token = data["tokens"][SystemRole.SALES]
    tech_token = data["tokens"][SystemRole.FIELD_TECHNICIAN]
    po_id = data["po_id"]
    project_id = data["project_id"]

    sales_headers = {"Authorization": f"Bearer {sales_token}"}
    tech_headers = {"Authorization": f"Bearer {tech_token}"}

    # Sales user should not be able to record supplier invoices or payments
    r1 = client.post(
        "/api/v1/supplier-invoices",
        json={"purchase_order_id": po_id, "invoice_number": "SINV-ERR", "subtotal": "1000", "total_amount": "1000"},
        headers=sales_headers,
    )
    assert r1.status_code == 403

    # Technician user should not be able to record project financial costs
    r2 = client.post(
        f"/api/v1/projects/{project_id}/costs",
        json={"cost_category": "LABOR", "cost_amount": "5000"},
        headers=tech_headers,
    )
    assert r2.status_code == 403
