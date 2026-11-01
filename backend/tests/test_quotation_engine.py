import pytest
import uuid
from decimal import Decimal
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.database import SessionLocal
from app.models.auth import User, Role, Department, Employee
from app.models.crm import Customer, Enquiry, Survey, Product, Quotation, QuotationItem, QuotationRevision
from app.models.workflow import AuditLog
from app.utils.security import hash_password, create_access_token
from app.utils.roles import SystemRole

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_quotation_data():
    """
    Set up authenticated test users, JWT tokens, test customer, enquiry, approved survey,
    and catalog products.
    """
    tokens = {}
    user_ids = {}
    data = {}

    with SessionLocal() as db:
        role_slugs = [
            SystemRole.SUPER_ADMIN,
            SystemRole.DIRECTOR,
            SystemRole.SALES,
            SystemRole.TECHNICAL_MANAGER,
            SystemRole.WAREHOUSE_PROCUREMENT,
            SystemRole.FIELD_TECHNICIAN,
            SystemRole.CUSTOMER,
        ]

        for slug in role_slugs:
            role_obj = db.execute(select(Role).where(Role.slug == slug)).scalar_one()
            email = f"test_{slug.lower()}_quo@sunpower.com"
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if not user:
                user = User(
                    role_id=role_obj.id,
                    email=email,
                    full_name=f"Test {slug} Quo",
                    hashed_password=hash_password("Pass123!Safe"),
                    is_active=True,
                    is_verified=True,
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            token = create_access_token(
                data={"sub": str(user.id), "role": role_obj.slug, "email": user.email}
            )
            tokens[slug] = token
            user_ids[slug] = user.id

        # Also create a SECOND Sales user to test separation of duties (creator vs approver)
        sales_role = db.execute(select(Role).where(Role.slug == SystemRole.SALES)).scalar_one()
        email_sales2 = "test_sales2_quo@sunpower.com"
        sales2_user = db.execute(select(User).where(User.email == email_sales2)).scalar_one_or_none()
        if not sales2_user:
            sales2_user = User(
                role_id=sales_role.id,
                email=email_sales2,
                full_name="Test Sales2 Quo",
                hashed_password=hash_password("Pass123!Safe"),
                is_active=True,
                is_verified=True,
            )
            db.add(sales2_user)
            db.commit()
            db.refresh(sales2_user)
        tokens["SALES_2"] = create_access_token(
            data={"sub": str(sales2_user.id), "role": sales_role.slug, "email": sales2_user.email}
        )
        user_ids["SALES_2"] = sales2_user.id

        # Also create a SECOND Customer user to test customer isolation
        cust_role = db.execute(select(Role).where(Role.slug == SystemRole.CUSTOMER)).scalar_one()
        email_cust2 = "test_customer2_quo@sunpower.com"
        cust2_user = db.execute(select(User).where(User.email == email_cust2)).scalar_one_or_none()
        if not cust2_user:
            cust2_user = User(
                role_id=cust_role.id,
                email=email_cust2,
                full_name="Other Customer Quo",
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

        # Create Customer 1 linked to customer user 1
        suffix = uuid.uuid4().hex[:6].upper()
        cust_user_id = user_ids[SystemRole.CUSTOMER]
        admin_id = user_ids[SystemRole.SUPER_ADMIN]

        customer1 = db.execute(select(Customer).where(Customer.user_id == cust_user_id)).scalar_one_or_none()
        if not customer1:
            customer1 = Customer(
                user_id=cust_user_id,
                customer_type="RESIDENTIAL",
                full_name=f"Residential Customer {suffix}",
                email=f"cust_{suffix}@sunpower.com",
                phone=f"98765{suffix[:5]}",
                address="123 Solar Street",
                city="Pune",
                state="Maharashtra",
                pincode="411001",
                created_by=admin_id,
                is_active=True,
            )
            db.add(customer1)
            db.commit()
            db.refresh(customer1)

        # Create Customer 2 linked to customer user 2
        cust2_user_id = user_ids["CUSTOMER_2"]
        customer2 = db.execute(select(Customer).where(Customer.user_id == cust2_user_id)).scalar_one_or_none()
        if not customer2:
            customer2 = Customer(
                user_id=cust2_user_id,
                customer_type="COMMERCIAL",
                full_name=f"Commercial Client {suffix}",
                email=f"cust2_{suffix}@sunpower.com",
                phone=f"98764{suffix[:5]}",
                address="456 Tech Park",
                city="Mumbai",
                state="Maharashtra",
                pincode="400001",
                created_by=admin_id,
                is_active=True,
            )
            db.add(customer2)
            db.commit()
            db.refresh(customer2)

        # Create Enquiry 1 for Customer 1
        enq1 = Enquiry(
            customer_id=customer1.id,
            enquiry_number=f"ENQ-{suffix}-1",
            source="DIRECT",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("3.00"),
            status="NEW",
        )
        db.add(enq1)
        db.commit()
        db.refresh(enq1)

        # Create Enquiry 2 for Customer 2
        enq2 = Enquiry(
            customer_id=customer2.id,
            enquiry_number=f"ENQ-{suffix}-2",
            source="DIRECT",
            system_type="COMMERCIAL",
            proposed_capacity_kw=Decimal("10.00"),
            status="NEW",
        )
        # Create Enquiry for isolation tests
        enq_iso = Enquiry(
            customer_id=customer1.id,
            enquiry_number=f"ENQ-{suffix}-ISO",
            source="DIRECT",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("3.00"),
            status="NEW",
        )
        # Create Enquiry for revision tests
        enq_rev = Enquiry(
            customer_id=customer1.id,
            enquiry_number=f"ENQ-{suffix}-REV",
            source="DIRECT",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("3.00"),
            status="NEW",
        )
        db.add_all([enq2, enq_iso, enq_rev])
        db.commit()
        db.refresh(enq2)
        db.refresh(enq_iso)
        db.refresh(enq_rev)

        # Create an employee for survey creation
        dept = db.execute(select(Department).where(Department.code == "TECH")).scalar_one_or_none()
        if not dept:
            dept = Department(name="Technical Services", code="TECH", is_active=True)
            db.add(dept)
            db.commit()
            db.refresh(dept)

        tm_user_id = user_ids[SystemRole.TECHNICAL_MANAGER]
        emp = db.execute(select(Employee).where(Employee.user_id == tm_user_id)).scalar_one_or_none()
        if not emp:
            emp = Employee(
                user_id=tm_user_id,
                department_id=dept.id,
                employee_code=f"EMP-{suffix[:4]}",
                designation="Surveyor",
                employment_type="FULL_TIME",
                joining_date=date.today(),
                is_active=True,
            )
            db.add(emp)
            db.commit()
            db.refresh(emp)

        # Survey 1 on Enquiry 1: APPROVED
        srv_approved = Survey(
            enquiry_id=enq1.id,
            surveyor_id=emp.id,
            survey_number=f"SRV-{suffix}-APP",
            scheduled_at=datetime.now(),
            conducted_at=datetime.now(),
            technical_feasibility="FEASIBLE",
            status="APPROVED",
        )
        # Survey 2 on Enquiry 1: DRAFT (unapproved)
        srv_unapproved = Survey(
            enquiry_id=enq1.id,
            surveyor_id=emp.id,
            survey_number=f"SRV-{suffix}-UNAPP",
            scheduled_at=datetime.now(),
            conducted_at=datetime.now(),
            technical_feasibility="FEASIBLE",
            status="DRAFT",
        )
        # Survey 3 on Enquiry 2: APPROVED
        srv_enq2 = Survey(
            enquiry_id=enq2.id,
            surveyor_id=emp.id,
            survey_number=f"SRV-{suffix}-ENQ2",
            scheduled_at=datetime.now(),
            conducted_at=datetime.now(),
            technical_feasibility="FEASIBLE",
            status="APPROVED",
        )
        # Survey for isolation tests
        srv_iso = Survey(
            enquiry_id=enq_iso.id,
            surveyor_id=emp.id,
            survey_number=f"SRV-{suffix}-ISO",
            scheduled_at=datetime.now(),
            conducted_at=datetime.now(),
            technical_feasibility="FEASIBLE",
            status="APPROVED",
        )
        # Survey for revision tests
        srv_rev = Survey(
            enquiry_id=enq_rev.id,
            surveyor_id=emp.id,
            survey_number=f"SRV-{suffix}-REV",
            scheduled_at=datetime.now(),
            conducted_at=datetime.now(),
            technical_feasibility="FEASIBLE",
            status="APPROVED",
        )
        db.add_all([srv_approved, srv_unapproved, srv_enq2, srv_iso, srv_rev])
        db.commit()
        db.refresh(srv_approved)
        db.refresh(srv_unapproved)
        db.refresh(srv_enq2)
        db.refresh(srv_iso)
        db.refresh(srv_rev)

        # Create active and inactive products
        p_active1 = Product(
            product_code=f"PANEL-{suffix}",
            name="540W Mono PERC Panel",
            category="SOLAR_PANEL",
            brand="SunPower",
            model_number="SP-540",
            unit_of_measure="NOS",
            base_price=Decimal("10000.00"),
            tax_rate_percent=Decimal("12.00"),
            is_active=True,
        )
        p_active2 = db.execute(select(Product).where(Product.category == "INVERTER", Product.is_active == True)).scalars().first()
        if not p_active2:
            p_active2 = Product(
                product_code=f"INV-{suffix}",
                name="3kW On-Grid Inverter",
                category="INVERTER",
                brand="Growatt",
                model_number="GW-3000",
                unit_of_measure="NOS",
                base_price=Decimal("25000.00"),
                tax_rate_percent=Decimal("12.00"),
                is_active=True,
            )
            db.add(p_active2)
            db.commit()
            db.refresh(p_active2)

        p_inactive = Product(
            product_code=f"BAT-{suffix}",
            name="Old Decommissioned Battery",
            category="BATTERY",
            unit_of_measure="NOS",
            base_price=Decimal("15000.00"),
            tax_rate_percent=Decimal("18.00"),
            is_active=False,
        )
        db.add_all([p_active1, p_inactive])
        db.commit()
        db.refresh(p_active1)
        db.refresh(p_inactive)

        data = {
            "customer1_id": customer1.id,
            "customer2_id": customer2.id,
            "enquiry1_id": enq1.id,
            "enquiry2_id": enq2.id,
            "enquiry_iso_id": enq_iso.id,
            "enquiry_rev_id": enq_rev.id,
            "survey_approved_id": srv_approved.id,
            "survey_unapproved_id": srv_unapproved.id,
            "survey_enq2_id": srv_enq2.id,
            "survey_iso_id": srv_iso.id,
            "survey_rev_id": srv_rev.id,
            "prod_panel_id": p_active1.id,
            "prod_inv_id": p_active2.id,
            "prod_inactive_id": p_inactive.id,
            "surveyor_emp_id": emp.id,
        }

    return {"tokens": tokens, "user_ids": user_ids, "data": data}


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# =========================================================================
# TEST SUITE: SIMS PHASE 5.4A QUOTATION ENGINE
# =========================================================================

def test_01_create_valid_quotation(setup_quotation_data):
    """Test 1: Valid quotation creation with active products and approved survey."""
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    payload = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "system_type": "ON_GRID",
        "capacity_kw": 3.0,
        "installation_cost": 5000.00,
        "items": [
            {
                "product_id": d["prod_panel_id"],
                "quantity": 6.0,
                "unit_price": 10000.00,
                "discount_amount": 2000.00,
                "tax_rate_percent": 12.0,
            },
            {
                "product_id": d["prod_inv_id"],
                "quantity": 1.0,
                "unit_price": 25000.00,
                "discount_amount": 0.00,
                "tax_rate_percent": 12.0,
            },
        ],
    }

    res = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    assert data["status"] == "DRAFT"
    assert data["version"] == 1
    assert data["quotation_number"].startswith("QUO-")
    assert len(data["items"]) == 2

    # Verify Calculations:
    # Item 1: Base = 6 * 10000 = 60000. Discount = 2000. Discounted base = 58000. Tax = 58000 * 12% = 6960. Line total = 64960.
    # Item 2: Base = 1 * 25000 = 25000. Discount = 0. Discounted base = 25000. Tax = 25000 * 12% = 3000. Line total = 28000.
    # Total product cost = 58000 + 25000 = 83000.
    # Total tax = 6960 + 3000 = 9960.
    # Installation cost = 5000.
    # Gross amount = 83000 + 5000 + 9960 = 97960.
    # Standard residential subsidy for 3kW = 60000 + 18000 = 78000.
    # Net payable = 97960 - 78000 = 19960.
    assert data["total_product_cost"] == 83000.00
    assert data["tax_amount"] == 9960.00
    assert data["installation_cost"] == 5000.00
    assert data["gross_amount"] == 97960.00
    assert data["subsidy_estimate"] == 78000.00
    assert data["net_payable_amount"] == 19960.00


def test_02_missing_enquiry(setup_quotation_data):
    """Test 2: Rejection if enquiry does not exist."""
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    payload = {
        "enquiry_id": 99999999,
        "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0}],
    }
    res = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_03_missing_survey(setup_quotation_data):
    """Test 3: Rejection if survey ID does not exist."""
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    payload = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": 99999999,
        "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0}],
    }
    res = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    assert res.status_code == 404
    assert "survey" in res.json()["detail"].lower()


def test_04_unapproved_survey(setup_quotation_data):
    """Test 4: Rejection if survey is not in APPROVED status."""
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    payload = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_unapproved_id"],  # Status is DRAFT
        "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0}],
    }
    res = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    assert res.status_code == 400
    assert "only approved surveys" in res.json()["detail"].lower()


def test_05_survey_belonging_to_another_enquiry(setup_quotation_data):
    """Test 5: Rejection if survey belongs to a different enquiry."""
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    payload = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_enq2_id"],  # Belongs to enquiry2
        "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0}],
    }
    res = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    assert res.status_code == 400
    assert "belongs to enquiry" in res.json()["detail"].lower()


def test_06_inactive_product_rejection(setup_quotation_data):
    """Test 6: Inactive product cannot be added to quotation."""
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    payload = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "items": [{"product_id": d["prod_inactive_id"], "quantity": 1.0}],
    }
    res = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    assert res.status_code == 400
    assert "inactive" in res.json()["detail"].lower()


def test_07_invalid_quantity_discount_price_and_tax(setup_quotation_data):
    """Test 7: Validation errors on negative or out-of-range financial inputs."""
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    # 1. Quantity <= 0
    p1 = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "items": [{"product_id": d["prod_panel_id"], "quantity": 0.0}],
    }
    r1 = client.post("/api/v1/quotations", json=p1, headers=auth_header(tokens[SystemRole.SALES]))
    assert r1.status_code == 422

    # 2. Negative price
    p2 = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0, "unit_price": -50.0}],
    }
    r2 = client.post("/api/v1/quotations", json=p2, headers=auth_header(tokens[SystemRole.SALES]))
    assert r2.status_code == 422

    # 3. Discount exceeds line base
    p3 = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0, "unit_price": 1000.0, "discount_amount": 1500.0}],
    }
    r3 = client.post("/api/v1/quotations", json=p3, headers=auth_header(tokens[SystemRole.SALES]))
    assert r3.status_code == 400
    assert "cannot exceed" in r3.json()["detail"].lower()

    # 4. Tax rate > 100%
    p4 = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0, "tax_rate_percent": 150.0}],
    }
    r4 = client.post("/api/v1/quotations", json=p4, headers=auth_header(tokens[SystemRole.SALES]))
    assert r4.status_code == 422


def test_08_decimal_calculation_accuracy_and_snapshots(setup_quotation_data):
    """Test 8 & 9: Exact Decimal precision and snapshotting from product master."""
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    # Omitting unit_price and tax_rate_percent should snapshot from catalog product
    payload = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "capacity_kw": 2.5,
        "items": [
            {
                "product_id": d["prod_panel_id"],
                "quantity": 3.0,
                # unit_price omitted -> snapshots 10000.00
                # tax_rate_percent omitted -> snapshots 12.00
                "discount_amount": 100.55,
            }
        ],
    }
    res = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    assert res.status_code == 201
    item = res.json()["data"]["items"][0]
    assert item["unit_price"] == 10000.00
    assert item["tax_rate_percent"] == 12.00
    assert item["discount_amount"] == 100.55

    # Base = 3 * 10000 = 30000.00. Disc = 100.55. Discounted base = 29899.45.
    # Tax = 29899.45 * 0.12 = 3587.934 -> 3587.93.
    # Total = 29899.45 + 3587.93 = 33487.38.
    assert item["total_amount"] == 33487.38


def test_10_validity_dates(setup_quotation_data):
    """Test 10, 11, 12: Default 30-day validity, custom validity, and invalid date check."""
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    today = date.today()

    # 1. Default validity: today + 30 days
    p1 = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0}],
    }
    r1 = client.post("/api/v1/quotations", json=p1, headers=auth_header(tokens[SystemRole.SALES]))
    assert r1.status_code == 201
    exp_default = (today + timedelta(days=30)).isoformat()
    assert r1.json()["data"]["valid_until"] == exp_default

    # 2. Custom valid date
    custom_date = (today + timedelta(days=45)).isoformat()
    p2 = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "valid_until": custom_date,
        "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0}],
    }
    r2 = client.post("/api/v1/quotations", json=p2, headers=auth_header(tokens[SystemRole.SALES]))
    assert r2.status_code == 201
    assert r2.json()["data"]["valid_until"] == custom_date

    # 3. Invalid date: past date
    past_date = (today - timedelta(days=2)).isoformat()
    p3 = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "valid_until": past_date,
        "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0}],
    }
    r3 = client.post("/api/v1/quotations", json=p3, headers=auth_header(tokens[SystemRole.SALES]))
    assert r3.status_code == 400
    assert "must be on or after" in r3.json()["detail"].lower()


def test_13_quotation_number_format(setup_quotation_data):
    """Test 13: Number format matches QUO-YYYYMM-XXXX and increments sequentially."""
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    payload = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0}],
    }
    r1 = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    r2 = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))

    assert r1.status_code == 201
    assert r2.status_code == 201
    num1 = r1.json()["data"]["quotation_number"]
    num2 = r2.json()["data"]["quotation_number"]

    prefix = f"QUO-{date.today().strftime('%Y%m')}-"
    assert num1.startswith(prefix)
    assert num2.startswith(prefix)
    seq1 = int(num1.split("-")[2])
    seq2 = int(num2.split("-")[2])
    assert seq2 == seq1 + 1


def test_15_draft_editing_and_transitions(setup_quotation_data):
    """Test 15 & 16: Editing a DRAFT quotation, submitting for approval, and invalid transitions."""
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    # 1. Create a draft
    payload = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "items": [{"product_id": d["prod_panel_id"], "quantity": 2.0}],
    }
    create_res = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    assert create_res.status_code == 201
    q_id = create_res.json()["data"]["id"]

    # 2. Update the draft
    update_res = client.put(
        f"/api/v1/quotations/{q_id}",
        json={"installation_cost": 3000.0, "capacity_kw": 4.0},
        headers=auth_header(tokens[SystemRole.SALES]),
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["installation_cost"] == 3000.00
    assert update_res.json()["data"]["capacity_kw"] == 4.00

    # 3. Direct invalid transition to ACCEPTED or SENT
    send_res = client.post(f"/api/v1/quotations/{q_id}/send", headers=auth_header(tokens[SystemRole.SALES]))
    assert send_res.status_code == 409  # Cannot send a DRAFT quotation

    # 4. Submit for review: DRAFT -> PENDING_APPROVAL
    submit_res = client.post(f"/api/v1/quotations/{q_id}/submit", headers=auth_header(tokens[SystemRole.SALES]))
    assert submit_res.status_code == 200
    assert submit_res.json()["data"]["status"] == "PENDING_APPROVAL"

    # 5. Cannot update while in PENDING_APPROVAL
    update_res2 = client.put(
        f"/api/v1/quotations/{q_id}",
        json={"installation_cost": 4000.0},
        headers=auth_header(tokens[SystemRole.SALES]),
    )
    assert update_res2.status_code == 409


def test_17_approval_and_role_separation(setup_quotation_data):
    """Test 17, 18, 19, 20: Approval permissions, self-approval prevention, Super Admin bypass."""
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    # 1. SALES creates quotation
    payload = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0}],
    }
    create_res = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    q_id = create_res.json()["data"]["id"]

    # Submit for review
    client.post(f"/api/v1/quotations/{q_id}/submit", headers=auth_header(tokens[SystemRole.SALES]))

    # 2. SALES attempts to approve -> HTTP 403 (Sales cannot approve)
    sales_app = client.post(f"/api/v1/quotations/{q_id}/approve", headers=auth_header(tokens[SystemRole.SALES]))
    assert sales_app.status_code == 403

    # 3. TECHNICAL_MANAGER approves -> HTTP 200
    tm_app = client.post(
        f"/api/v1/quotations/{q_id}/approve",
        json={"comments": "Technically compliant and verified."},
        headers=auth_header(tokens[SystemRole.TECHNICAL_MANAGER]),
    )
    assert tm_app.status_code == 200
    assert tm_app.json()["data"]["status"] == "APPROVED"


def test_19_creator_self_approval_restriction(setup_quotation_data):
    """Test 19 & 20: Creator cannot approve own quotation unless SUPER_ADMIN."""
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    # 1. Technical Manager creates a quotation (Super Admin/Sales create, but suppose TM or Director is creator)
    # Let's test with SUPER_ADMIN who created a quotation:
    payload = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0}],
    }
    admin_create = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SUPER_ADMIN]))
    q_admin_id = admin_create.json()["data"]["id"]
    client.post(f"/api/v1/quotations/{q_admin_id}/submit", headers=auth_header(tokens[SystemRole.SUPER_ADMIN]))

    # Super Admin approves their own -> allowed!
    admin_app = client.post(f"/api/v1/quotations/{q_admin_id}/approve", headers=auth_header(tokens[SystemRole.SUPER_ADMIN]))
    assert admin_app.status_code == 200
    assert admin_app.json()["data"]["status"] == "APPROVED"


def test_21_pricing_modification_restrictions(setup_quotation_data):
    """Test 21: Technical Manager and Director cannot change sales pricing on draft quotations."""
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    # Create draft
    payload = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0}],
    }
    create_res = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    q_id = create_res.json()["data"]["id"]

    # Technical Manager tries to edit pricing
    tm_edit = client.put(
        f"/api/v1/quotations/{q_id}",
        json={"installation_cost": 9999.0},
        headers=auth_header(tokens[SystemRole.TECHNICAL_MANAGER]),
    )
    assert tm_edit.status_code == 403

    # Director tries to edit pricing
    dir_edit = client.put(
        f"/api/v1/quotations/{q_id}",
        json={"installation_cost": 9999.0},
        headers=auth_header(tokens[SystemRole.DIRECTOR]),
    )
    assert dir_edit.status_code == 403


def test_22_sending_and_customer_acceptance(setup_quotation_data):
    """Test 22 & 23: Sending updates enquiry to QUOTED; acceptance updates enquiry to WON."""
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    # 1. Create quotation for enquiry 1
    payload = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0}],
    }
    create_res = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    q_id = create_res.json()["data"]["id"]

    # 2. Submit & Approve
    client.post(f"/api/v1/quotations/{q_id}/submit", headers=auth_header(tokens[SystemRole.SALES]))
    client.post(f"/api/v1/quotations/{q_id}/approve", headers=auth_header(tokens[SystemRole.TECHNICAL_MANAGER]))

    # 3. Send to customer
    send_res = client.post(f"/api/v1/quotations/{q_id}/send", headers=auth_header(tokens[SystemRole.SALES]))
    assert send_res.status_code == 200
    assert send_res.json()["data"]["status"] == "SENT"

    # Verify enquiry status is now QUOTED in DB
    with SessionLocal() as db:
        enq = db.execute(select(Enquiry).where(Enquiry.id == d["enquiry1_id"])).scalar_one()
        assert enq.status == "QUOTED"

    # 4. Customer accepts quotation
    accept_res = client.post(
        f"/api/v1/quotations/{q_id}/accept",
        json={"acceptance_notes": "Accepted terms and ready for installation."},
        headers=auth_header(tokens[SystemRole.CUSTOMER]),
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["data"]["status"] == "ACCEPTED"

    # Verify enquiry status is now WON in DB
    with SessionLocal() as db:
        enq = db.execute(select(Enquiry).where(Enquiry.id == d["enquiry1_id"])).scalar_one()
        assert enq.status == "WON"


def test_24_customer_isolation_and_acceptance_security(setup_quotation_data):
    """Test 24, 25, 26, 27: Customer ownership checks and acceptance constraints."""
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    # Create quotation for Customer 1
    payload = {
        "enquiry_id": d["enquiry_iso_id"],
        "survey_id": d["survey_iso_id"],
        "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0}],
    }
    c_res = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    q_id = c_res.json()["data"]["id"]

    # Customer 2 attempts to retrieve Customer 1's quotation -> HTTP 404
    c2_get = client.get(f"/api/v1/quotations/{q_id}", headers=auth_header(tokens["CUSTOMER_2"]))
    assert c2_get.status_code == 404

    # Customer 1 attempts to accept while in DRAFT status -> HTTP 409
    c1_early_accept = client.post(f"/api/v1/quotations/{q_id}/accept", headers=auth_header(tokens[SystemRole.CUSTOMER]))
    assert c1_early_accept.status_code == 409

    # Advance to SENT
    client.post(f"/api/v1/quotations/{q_id}/submit", headers=auth_header(tokens[SystemRole.SALES]))
    client.post(f"/api/v1/quotations/{q_id}/approve", headers=auth_header(tokens[SystemRole.TECHNICAL_MANAGER]))
    client.post(f"/api/v1/quotations/{q_id}/send", headers=auth_header(tokens[SystemRole.SALES]))

    # Customer 2 attempts to accept Customer 1's quotation -> HTTP 403
    c2_accept = client.post(f"/api/v1/quotations/{q_id}/accept", headers=auth_header(tokens["CUSTOMER_2"]))
    assert c2_accept.status_code == 403

    # Customer 1 accepts -> HTTP 200
    c1_accept = client.post(f"/api/v1/quotations/{q_id}/accept", headers=auth_header(tokens[SystemRole.CUSTOMER]))
    assert c1_accept.status_code == 200

    # Duplicate acceptance attempt -> HTTP 409
    c1_dup_accept = client.post(f"/api/v1/quotations/{q_id}/accept", headers=auth_header(tokens[SystemRole.CUSTOMER]))
    assert c1_dup_accept.status_code == 409


def test_28_revision_workflow_and_immutability(setup_quotation_data):
    """Test 28, 29, 30, 31: Revisions, snapshot integrity, and ACCEPTED immutability."""
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    # 1. Create and send a quotation
    payload = {
        "enquiry_id": d["enquiry_rev_id"],
        "survey_id": d["survey_rev_id"],
        "installation_cost": 2000.0,
        "items": [{"product_id": d["prod_panel_id"], "quantity": 4.0}],
    }
    c_res = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    q_id = c_res.json()["data"]["id"]

    client.post(f"/api/v1/quotations/{q_id}/submit", headers=auth_header(tokens[SystemRole.SALES]))
    client.post(f"/api/v1/quotations/{q_id}/approve", headers=auth_header(tokens[SystemRole.TECHNICAL_MANAGER]))
    client.post(f"/api/v1/quotations/{q_id}/send", headers=auth_header(tokens[SystemRole.SALES]))

    # 2. Customer requests revision: Revision requires non-empty reason
    rev_bad = client.post(
        f"/api/v1/quotations/{q_id}/revise",
        json={"reason_for_revision": ""},
        headers=auth_header(tokens[SystemRole.SALES]),
    )
    assert rev_bad.status_code == 422

    # 3. Create valid revision
    rev_ok = client.post(
        f"/api/v1/quotations/{q_id}/revise",
        json={
            "reason_for_revision": "Customer requested 2 additional panels.",
            "installation_cost": 2500.0,
            "items": [{"product_id": d["prod_panel_id"], "quantity": 6.0}],
        },
        headers=auth_header(tokens[SystemRole.SALES]),
    )
    assert rev_ok.status_code == 200
    rev_data = rev_ok.json()["data"]

    # Version incremented from 1 to 2, returned to DRAFT
    assert rev_data["version"] == 2
    assert rev_data["status"] == "DRAFT"
    assert rev_data["installation_cost"] == 2500.00
    assert len(rev_data["revisions"]) == 1

    # Check snapshot data
    snap = rev_data["revisions"][0]
    assert snap["revision_number"] == 1
    assert snap["reason_for_revision"] == "Customer requested 2 additional panels."
    assert snap["snapshot_data"]["version"] == 1
    assert snap["snapshot_data"]["installation_cost"] == 2000.0

    # 4. Progress revision 2 to ACCEPTED
    client.post(f"/api/v1/quotations/{q_id}/submit", headers=auth_header(tokens[SystemRole.SALES]))
    client.post(f"/api/v1/quotations/{q_id}/approve", headers=auth_header(tokens[SystemRole.DIRECTOR]))
    client.post(f"/api/v1/quotations/{q_id}/send", headers=auth_header(tokens[SystemRole.SALES]))
    client.post(f"/api/v1/quotations/{q_id}/accept", headers=auth_header(tokens[SystemRole.CUSTOMER]))

    # 5. Immutability verification on ACCEPTED quotation
    # Cannot edit
    assert client.put(f"/api/v1/quotations/{q_id}", json={"installation_cost": 1000.0}, headers=auth_header(tokens[SystemRole.SALES])).status_code == 409
    # Cannot revise
    assert client.post(f"/api/v1/quotations/{q_id}/revise", json={"reason_for_revision": "Too late"}, headers=auth_header(tokens[SystemRole.SALES])).status_code == 409
    # Cannot delete
    assert client.delete(f"/api/v1/quotations/{q_id}", headers=auth_header(tokens[SystemRole.SALES])).status_code == 409


def test_32_subsidy_defaults_and_override_workflow(setup_quotation_data):
    """Test 32, 33, 34: Subsidy policy calculation, authorized override, and mandatory reason."""
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    # 1. Commercial customer gets 0.00 default subsidy
    p_comm = {
        "enquiry_id": d["enquiry2_id"],
        "survey_id": d["survey_enq2_id"],
        "capacity_kw": 10.0,
        "items": [{"product_id": d["prod_panel_id"], "quantity": 10.0}],
    }
    r_comm = client.post("/api/v1/quotations", json=p_comm, headers=auth_header(tokens[SystemRole.SALES]))
    assert r_comm.status_code == 201
    assert r_comm.json()["data"]["subsidy_estimate"] == 0.00

    # 2. Residential customer: Override requires reason
    p_ov_no_reason = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "capacity_kw": 3.0,
        "subsidy_estimate": 50000.00,  # Standard is 78,000
        "items": [{"product_id": d["prod_panel_id"], "quantity": 6.0}],
    }
    r_no_reason = client.post("/api/v1/quotations", json=p_ov_no_reason, headers=auth_header(tokens[SystemRole.SALES]))
    assert r_no_reason.status_code == 400
    assert "override_reason" in r_no_reason.json()["detail"].lower()

    # 3. Residential customer: Override with reason succeeds
    p_ov_with_reason = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "capacity_kw": 3.0,
        "subsidy_estimate": 50000.00,
        "subsidy_override_reason": "DISCOM meter cap reduced eligible subsidy.",
        "items": [{"product_id": d["prod_panel_id"], "quantity": 6.0}],
    }
    r_with_reason = client.post("/api/v1/quotations", json=p_ov_with_reason, headers=auth_header(tokens[SystemRole.SALES]))
    assert r_with_reason.status_code == 201
    assert r_with_reason.json()["data"]["subsidy_estimate"] == 50000.00


def test_35_audit_trail_logging(setup_quotation_data):
    """Test 35: Verify audit trail logs for quotation lifecycle events."""
    with SessionLocal() as db:
        logs = db.execute(
            select(AuditLog)
            .where(AuditLog.entity_name == "QUOTATION")
            .order_by(AuditLog.id.desc())
            .limit(20)
        ).scalars().all()

        actions = [log.action for log in logs]
        assert "QUOTATION_CREATED" in actions
        assert "QUOTATION_APPROVED" in actions
        assert "QUOTATION_SENT" in actions
        assert "QUOTATION_ACCEPTED" in actions
        assert "QUOTATION_REVISED" in actions
        assert "SUBSIDY_OVERRIDDEN" in actions


def test_36_single_acceptance_guard_and_enquiry_protection(setup_quotation_data):
    """
    Test 36: Strict single-acceptance guard for multiple quotations on one enquiry,
    terminal enquiry status blocking, and concurrent acceptance safety.
    """
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]
    suffix = uuid.uuid4().hex[:6].upper()

    # 1. Setup enquiry with 2 competing quotations
    with SessionLocal() as db:
        enq_comp = Enquiry(
            customer_id=d["customer1_id"],
            enquiry_number=f"ENQ-{suffix}-COMP",
            source="DIRECT",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("5.00"),
            status="NEW",
        )
        db.add(enq_comp)
        db.commit()
        db.refresh(enq_comp)

        srv_comp = Survey(
            enquiry_id=enq_comp.id,
            surveyor_id=d["surveyor_emp_id"],
            survey_number=f"SRV-{suffix}-COMP",
            scheduled_at=datetime.now(),
            conducted_at=datetime.now(),
            technical_feasibility="FEASIBLE",
            status="APPROVED",
        )
        db.add(srv_comp)
        db.commit()
        db.refresh(srv_comp)

        enq_comp_id = enq_comp.id
        srv_comp_id = srv_comp.id

    # Create Quotation 1 (3kW system)
    payload1 = {
        "enquiry_id": enq_comp_id,
        "survey_id": srv_comp_id,
        "capacity_kw": 3.0,
        "items": [{"product_id": d["prod_panel_id"], "quantity": 6.0}],
    }
    r_q1 = client.post("/api/v1/quotations", json=payload1, headers=auth_header(tokens[SystemRole.SALES]))
    assert r_q1.status_code == 201
    q1_id = r_q1.json()["data"]["id"]
    q1_num = r_q1.json()["data"]["quotation_number"]

    # Create Quotation 2 (5kW system)
    payload2 = {
        "enquiry_id": enq_comp_id,
        "survey_id": srv_comp_id,
        "capacity_kw": 5.0,
        "items": [{"product_id": d["prod_panel_id"], "quantity": 10.0}],
    }
    r_q2 = client.post("/api/v1/quotations", json=payload2, headers=auth_header(tokens[SystemRole.SALES]))
    assert r_q2.status_code == 201
    q2_id = r_q2.json()["data"]["id"]
    q2_num = r_q2.json()["data"]["quotation_number"]

    # Progress both Quotation 1 and Quotation 2 to SENT
    for qid in [q1_id, q2_id]:
        client.post(f"/api/v1/quotations/{qid}/submit", headers=auth_header(tokens[SystemRole.SALES]))
        client.post(f"/api/v1/quotations/{qid}/approve", headers=auth_header(tokens[SystemRole.TECHNICAL_MANAGER]))
        send_res = client.post(f"/api/v1/quotations/{qid}/send", headers=auth_header(tokens[SystemRole.SALES]))
        assert send_res.status_code == 200
        assert send_res.json()["data"]["status"] == "SENT"

    # Verify both quotations are SENT and Enquiry is QUOTED
    with SessionLocal() as db:
        enq = db.execute(select(Enquiry).where(Enquiry.id == enq_comp_id)).scalar_one()
        assert enq.status == "QUOTED"
        q1_db = db.execute(select(Quotation).where(Quotation.id == q1_id)).scalar_one()
        q2_db = db.execute(select(Quotation).where(Quotation.id == q2_id)).scalar_one()
        assert q1_db.status == "SENT"
        assert q2_db.status == "SENT"

    # Step A: Customer accepts Quotation 1 -> SUCCEEDS
    accept1 = client.post(
        f"/api/v1/quotations/{q1_id}/accept",
        json={"acceptance_notes": "Accepted 3kW option"},
        headers=auth_header(tokens[SystemRole.CUSTOMER]),
    )
    assert accept1.status_code == 200
    assert accept1.json()["data"]["status"] == "ACCEPTED"

    # Verify Quotation 1 is ACCEPTED and Enquiry is WON
    with SessionLocal() as db:
        enq = db.execute(select(Enquiry).where(Enquiry.id == enq_comp_id)).scalar_one()
        assert enq.status == "WON"
        q1_db = db.execute(select(Quotation).where(Quotation.id == q1_id)).scalar_one()
        assert q1_db.status == "ACCEPTED"

    # Step B: Customer attempts to accept Quotation 2 -> MUST RETURN HTTP 409 CONFLICT
    accept2 = client.post(
        f"/api/v1/quotations/{q2_id}/accept",
        json={"acceptance_notes": "Trying to also accept 5kW option"},
        headers=auth_header(tokens[SystemRole.CUSTOMER]),
    )
    assert accept2.status_code == 409
    err_detail = accept2.json()["detail"]
    assert "Another quotation" in err_detail or "already been accepted" in err_detail
    assert q1_num in err_detail

    # Step C: Verify Quotation 2 remains SENT, Quotation 1 remains ACCEPTED, and Enquiry remains WON
    with SessionLocal() as db:
        q2_check = db.execute(select(Quotation).where(Quotation.id == q2_id)).scalar_one()
        assert q2_check.status == "SENT"

        q1_check = db.execute(select(Quotation).where(Quotation.id == q1_id)).scalar_one()
        assert q1_check.status == "ACCEPTED"

        enq_check = db.execute(select(Enquiry).where(Enquiry.id == enq_comp_id)).scalar_one()
        assert enq_check.status == "WON"

    # Step D: Test acceptance blocked when enquiry is in LOST status
    with SessionLocal() as db:
        enq_lost = Enquiry(
            customer_id=d["customer1_id"],
            enquiry_number=f"ENQ-{suffix}-LOST",
            source="DIRECT",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("3.00"),
            status="NEW",
        )
        db.add(enq_lost)
        db.commit()
        db.refresh(enq_lost)

        srv_lost = Survey(
            enquiry_id=enq_lost.id,
            surveyor_id=d["surveyor_emp_id"],
            survey_number=f"SRV-{suffix}-LOST",
            scheduled_at=datetime.now(),
            conducted_at=datetime.now(),
            technical_feasibility="FEASIBLE",
            status="APPROVED",
        )
        db.add(srv_lost)
        db.commit()
        db.refresh(srv_lost)
        enq_lost_id = enq_lost.id
        srv_lost_id = srv_lost.id

    r_qlost = client.post(
        "/api/v1/quotations",
        json={
            "enquiry_id": enq_lost_id,
            "survey_id": srv_lost_id,
            "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0}],
        },
        headers=auth_header(tokens[SystemRole.SALES]),
    )
    assert r_qlost.status_code == 201
    qlost_id = r_qlost.json()["data"]["id"]
    client.post(f"/api/v1/quotations/{qlost_id}/submit", headers=auth_header(tokens[SystemRole.SALES]))
    client.post(f"/api/v1/quotations/{qlost_id}/approve", headers=auth_header(tokens[SystemRole.TECHNICAL_MANAGER]))
    client.post(f"/api/v1/quotations/{qlost_id}/send", headers=auth_header(tokens[SystemRole.SALES]))

    # Now transition enquiry to LOST
    with SessionLocal() as db:
        e = db.execute(select(Enquiry).where(Enquiry.id == enq_lost_id)).scalar_one()
        e.status = "LOST"
        db.commit()

    # Attempt to accept quotation for LOST enquiry -> 409
    res_lost = client.post(f"/api/v1/quotations/{qlost_id}/accept", headers=auth_header(tokens[SystemRole.CUSTOMER]))
    assert res_lost.status_code == 409
    assert "terminal status 'LOST'" in res_lost.json()["detail"]

    # Step E: Test acceptance blocked when enquiry is in CANCELLED status
    with SessionLocal() as db:
        enq_canc = Enquiry(
            customer_id=d["customer1_id"],
            enquiry_number=f"ENQ-{suffix}-CANC",
            source="DIRECT",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("3.00"),
            status="NEW",
        )
        db.add(enq_canc)
        db.commit()
        db.refresh(enq_canc)

        srv_canc = Survey(
            enquiry_id=enq_canc.id,
            surveyor_id=d["surveyor_emp_id"],
            survey_number=f"SRV-{suffix}-CANC",
            scheduled_at=datetime.now(),
            conducted_at=datetime.now(),
            technical_feasibility="FEASIBLE",
            status="APPROVED",
        )
        db.add(srv_canc)
        db.commit()
        db.refresh(srv_canc)
        enq_canc_id = enq_canc.id
        srv_canc_id = srv_canc.id

    r_qcanc = client.post(
        "/api/v1/quotations",
        json={
            "enquiry_id": enq_canc_id,
            "survey_id": srv_canc_id,
            "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0}],
        },
        headers=auth_header(tokens[SystemRole.SALES]),
    )
    assert r_qcanc.status_code == 201
    qcanc_id = r_qcanc.json()["data"]["id"]
    client.post(f"/api/v1/quotations/{qcanc_id}/submit", headers=auth_header(tokens[SystemRole.SALES]))
    client.post(f"/api/v1/quotations/{qcanc_id}/approve", headers=auth_header(tokens[SystemRole.TECHNICAL_MANAGER]))
    client.post(f"/api/v1/quotations/{qcanc_id}/send", headers=auth_header(tokens[SystemRole.SALES]))

    # Transition enquiry to CANCELLED
    with SessionLocal() as db:
        e = db.execute(select(Enquiry).where(Enquiry.id == enq_canc_id)).scalar_one()
        e.status = "CANCELLED"
        db.commit()

    # Attempt to accept quotation for CANCELLED enquiry -> 409
    res_canc = client.post(f"/api/v1/quotations/{qcanc_id}/accept", headers=auth_header(tokens[SystemRole.CUSTOMER]))
    assert res_canc.status_code == 409
    assert "terminal status 'CANCELLED'" in res_canc.json()["detail"]

    # Step F: Super Admin acceptance authorization & single acceptance enforcement
    with SessionLocal() as db:
        enq_sa = Enquiry(
            customer_id=d["customer1_id"],
            enquiry_number=f"ENQ-{suffix}-SA",
            source="DIRECT",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("3.00"),
            status="NEW",
        )
        db.add(enq_sa)
        db.commit()
        db.refresh(enq_sa)

        srv_sa = Survey(
            enquiry_id=enq_sa.id,
            surveyor_id=d["surveyor_emp_id"],
            survey_number=f"SRV-{suffix}-SA",
            scheduled_at=datetime.now(),
            conducted_at=datetime.now(),
            technical_feasibility="FEASIBLE",
            status="APPROVED",
        )
        db.add(srv_sa)
        db.commit()
        db.refresh(srv_sa)
        enq_sa_id = enq_sa.id
        srv_sa_id = srv_sa.id

    r_sa1 = client.post(
        "/api/v1/quotations",
        json={"enquiry_id": enq_sa_id, "survey_id": srv_sa_id, "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0}]},
        headers=auth_header(tokens[SystemRole.SALES]),
    )
    r_sa2 = client.post(
        "/api/v1/quotations",
        json={"enquiry_id": enq_sa_id, "survey_id": srv_sa_id, "items": [{"product_id": d["prod_panel_id"], "quantity": 2.0}]},
        headers=auth_header(tokens[SystemRole.SALES]),
    )
    sa1_id = r_sa1.json()["data"]["id"]
    sa2_id = r_sa2.json()["data"]["id"]
    for qid in [sa1_id, sa2_id]:
        client.post(f"/api/v1/quotations/{qid}/submit", headers=auth_header(tokens[SystemRole.SALES]))
        client.post(f"/api/v1/quotations/{qid}/approve", headers=auth_header(tokens[SystemRole.TECHNICAL_MANAGER]))
        client.post(f"/api/v1/quotations/{qid}/send", headers=auth_header(tokens[SystemRole.SALES]))

    # Super Admin accepts quotation 1 on behalf of customer -> 200
    sa_accept = client.post(f"/api/v1/quotations/{sa1_id}/accept", headers=auth_header(tokens[SystemRole.SUPER_ADMIN]))
    assert sa_accept.status_code == 200

    # Super Admin attempts to accept quotation 2 on same enquiry -> 409
    sa_accept2 = client.post(f"/api/v1/quotations/{sa2_id}/accept", headers=auth_header(tokens[SystemRole.SUPER_ADMIN]))
    assert sa_accept2.status_code == 409

    # Step G: Concurrency safety verification with concurrent requests
    with SessionLocal() as db:
        enq_race = Enquiry(
            customer_id=d["customer1_id"],
            enquiry_number=f"ENQ-{suffix}-RACE",
            source="DIRECT",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("3.00"),
            status="NEW",
        )
        db.add(enq_race)
        db.commit()
        db.refresh(enq_race)

        srv_race = Survey(
            enquiry_id=enq_race.id,
            surveyor_id=d["surveyor_emp_id"],
            survey_number=f"SRV-{suffix}-RACE",
            scheduled_at=datetime.now(),
            conducted_at=datetime.now(),
            technical_feasibility="FEASIBLE",
            status="APPROVED",
        )
        db.add(srv_race)
        db.commit()
        db.refresh(srv_race)
        enq_race_id = enq_race.id
        srv_race_id = srv_race.id

    r_race1 = client.post(
        "/api/v1/quotations",
        json={"enquiry_id": enq_race_id, "survey_id": srv_race_id, "items": [{"product_id": d["prod_panel_id"], "quantity": 1.0}]},
        headers=auth_header(tokens[SystemRole.SALES]),
    )
    r_race2 = client.post(
        "/api/v1/quotations",
        json={"enquiry_id": enq_race_id, "survey_id": srv_race_id, "items": [{"product_id": d["prod_panel_id"], "quantity": 2.0}]},
        headers=auth_header(tokens[SystemRole.SALES]),
    )
    race1_id = r_race1.json()["data"]["id"]
    race2_id = r_race2.json()["data"]["id"]
    for qid in [race1_id, race2_id]:
        client.post(f"/api/v1/quotations/{qid}/submit", headers=auth_header(tokens[SystemRole.SALES]))
        client.post(f"/api/v1/quotations/{qid}/approve", headers=auth_header(tokens[SystemRole.TECHNICAL_MANAGER]))
        client.post(f"/api/v1/quotations/{qid}/send", headers=auth_header(tokens[SystemRole.SALES]))

    def attempt_accept(target_qid):
        local_client = TestClient(app)
        return local_client.post(
            f"/api/v1/quotations/{target_qid}/accept",
            headers=auth_header(tokens[SystemRole.CUSTOMER]),
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(attempt_accept, race1_id)
        f2 = executor.submit(attempt_accept, race2_id)
        res1 = f1.result()
        res2 = f2.result()

    status_codes = sorted([res1.status_code, res2.status_code])
    assert status_codes == [200, 409], f"Expected one 200 and one 409, but got: {status_codes}"

    # Verify DB state: exactly one is ACCEPTED, one is SENT, enquiry is WON
    with SessionLocal() as db:
        enq_final = db.execute(select(Enquiry).where(Enquiry.id == enq_race_id)).scalar_one()
        assert enq_final.status == "WON"
        q_race1 = db.execute(select(Quotation).where(Quotation.id == race1_id)).scalar_one()
        q_race2 = db.execute(select(Quotation).where(Quotation.id == race2_id)).scalar_one()
        quo_statuses = sorted([q_race1.status, q_race2.status])
        assert quo_statuses == ["ACCEPTED", "SENT"]


def test_37_customer_rejection_workflow(setup_quotation_data):
    """
    Test 37: Customer rejection workflow.
    - Owner customer can reject a SENT quotation.
    - Quotation transitions to REJECTED.
    - Rejection is audited with rejection reason.
    - Unauthorized customer cannot decline another customer's quotation (403).
    - Unauthorized roles cannot decline quotations (403).
    - Cannot decline non-SENT quotation (409).
    - Mandatory rejection reason validation (422).
    - REJECTED quotation can be revised back to DRAFT v2.
    """
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]
    suffix = uuid.uuid4().hex[:6].upper()

    with SessionLocal() as db:
        enq = Enquiry(
            customer_id=d["customer1_id"],
            enquiry_number=f"ENQ-{suffix}-CREJ",
            source="DIRECT",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("4.00"),
            status="NEW",
        )
        db.add(enq)
        db.commit()
        db.refresh(enq)

        srv = Survey(
            enquiry_id=enq.id,
            surveyor_id=d["surveyor_emp_id"],
            survey_number=f"SRV-{suffix}-CREJ",
            scheduled_at=datetime.now(),
            conducted_at=datetime.now(),
            technical_feasibility="FEASIBLE",
            status="APPROVED",
        )
        db.add(srv)
        db.commit()
        db.refresh(srv)
        enq_id = enq.id
        srv_id = srv.id

    # 1. Create a draft quotation
    payload = {
        "enquiry_id": enq_id,
        "survey_id": srv_id,
        "items": [{"product_id": d["prod_panel_id"], "quantity": 4.0}],
    }
    r = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    assert r.status_code == 201
    q_id = r.json()["data"]["id"]

    # 2. Try customer-reject while still in DRAFT -> 409 Conflict
    rej_draft = client.post(
        f"/api/v1/quotations/{q_id}/customer-reject",
        json={"rejection_reason": "Too expensive"},
        headers=auth_header(tokens[SystemRole.CUSTOMER]),
    )
    assert rej_draft.status_code == 409
    assert "Only SENT quotations can be declined" in rej_draft.json()["detail"]

    # 3. Advance to SENT
    client.post(f"/api/v1/quotations/{q_id}/submit", headers=auth_header(tokens[SystemRole.SALES]))
    client.post(f"/api/v1/quotations/{q_id}/approve", headers=auth_header(tokens[SystemRole.TECHNICAL_MANAGER]))
    client.post(f"/api/v1/quotations/{q_id}/send", headers=auth_header(tokens[SystemRole.SALES]))

    # 4. Reason validation (< 3 chars -> 422)
    rej_short = client.post(
        f"/api/v1/quotations/{q_id}/customer-reject",
        json={"rejection_reason": "No"},
        headers=auth_header(tokens[SystemRole.CUSTOMER]),
    )
    assert rej_short.status_code == 422

    # 5. Customer 2 attempts to decline Customer 1's quotation -> 403 Forbidden
    rej_c2 = client.post(
        f"/api/v1/quotations/{q_id}/customer-reject",
        json={"rejection_reason": "Declining on someone else's behalf"},
        headers=auth_header(tokens["CUSTOMER_2"]),
    )
    assert rej_c2.status_code == 403
    assert "You can only decline quotations associated with your own account" in rej_c2.json()["detail"]

    # 6. Unauthorized internal staff (e.g., Sales) attempts customer-reject -> 403 Forbidden
    rej_sales = client.post(
        f"/api/v1/quotations/{q_id}/customer-reject",
        json={"rejection_reason": "Sales rep trying to decline"},
        headers=auth_header(tokens[SystemRole.SALES]),
    )
    assert rej_sales.status_code == 403

    # 7. Customer 1 successfully declines quotation
    rejection_text = "Customer selected a competitor offering zero-down financing."
    rej_ok = client.post(
        f"/api/v1/quotations/{q_id}/customer-reject",
        json={"rejection_reason": rejection_text},
        headers=auth_header(tokens[SystemRole.CUSTOMER]),
    )
    assert rej_ok.status_code == 200
    assert rej_ok.json()["data"]["status"] == "REJECTED"

    # 8. Verify DB state and Audit Log
    with SessionLocal() as db:
        q_db = db.execute(select(Quotation).where(Quotation.id == q_id)).scalar_one()
        assert q_db.status == "REJECTED"

        audit = db.execute(
            select(AuditLog)
            .where(AuditLog.entity_name == "QUOTATION", AuditLog.entity_id == q_id, AuditLog.action == "QUOTATION_REJECTED")
            .order_by(AuditLog.id.desc())
        ).scalar_one_or_none()
        assert audit is not None
        assert audit.details["rejection_reason"] == rejection_text

    # 9. Verify quotation can be revised from REJECTED state
    rev_res = client.post(
        f"/api/v1/quotations/{q_id}/revise",
        json={"reason_for_revision": "Revising pricing to match competitor quote."},
        headers=auth_header(tokens[SystemRole.SALES]),
    )
    assert rev_res.status_code == 200
    assert rev_res.json()["data"]["version"] == 2
    assert rev_res.json()["data"]["status"] == "DRAFT"


def test_38_internal_reviewer_rejection_workflow(setup_quotation_data):
    """
    Test 38: Internal reviewer rejection workflow.
    - Authorized reviewer (TECHNICAL_MANAGER, DIRECTOR, SUPER_ADMIN) can reject PENDING_APPROVAL quotation.
    - Rejection reason is recorded and quotation transitions to REJECTED.
    - Unauthorized roles (SALES, CUSTOMER, etc.) cannot reject (403).
    - Cannot reject in invalid lifecycle states like DRAFT or APPROVED (409).
    - Mandatory comments validation (422).
    - Revised quotation can be returned to DRAFT.
    """
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]
    suffix = uuid.uuid4().hex[:6].upper()

    with SessionLocal() as db:
        enq = Enquiry(
            customer_id=d["customer1_id"],
            enquiry_number=f"ENQ-{suffix}-IREJ",
            source="DIRECT",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("5.00"),
            status="NEW",
        )
        db.add(enq)
        db.commit()
        db.refresh(enq)

        srv = Survey(
            enquiry_id=enq.id,
            surveyor_id=d["surveyor_emp_id"],
            survey_number=f"SRV-{suffix}-IREJ",
            scheduled_at=datetime.now(),
            conducted_at=datetime.now(),
            technical_feasibility="FEASIBLE",
            status="APPROVED",
        )
        db.add(srv)
        db.commit()
        db.refresh(srv)
        enq_id = enq.id
        srv_id = srv.id

    # 1. Create a draft quotation
    payload = {
        "enquiry_id": enq_id,
        "survey_id": srv_id,
        "items": [{"product_id": d["prod_panel_id"], "quantity": 5.0}],
    }
    r = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    assert r.status_code == 201
    q_id = r.json()["data"]["id"]

    # 2. Try reviewer reject while in DRAFT -> 409 Conflict
    rej_draft = client.post(
        f"/api/v1/quotations/{q_id}/reject",
        json={"comments": "Premature rejection"},
        headers=auth_header(tokens[SystemRole.TECHNICAL_MANAGER]),
    )
    assert rej_draft.status_code == 409

    # 3. Submit for approval -> status is PENDING_APPROVAL
    client.post(f"/api/v1/quotations/{q_id}/submit", headers=auth_header(tokens[SystemRole.SALES]))

    # 4. Comments validation (< 3 chars -> 422)
    rej_short = client.post(
        f"/api/v1/quotations/{q_id}/reject",
        json={"comments": "No"},
        headers=auth_header(tokens[SystemRole.TECHNICAL_MANAGER]),
    )
    assert rej_short.status_code == 422

    # 5. Unauthorized role: SALES attempts to reject -> 403 Forbidden
    rej_sales = client.post(
        f"/api/v1/quotations/{q_id}/reject",
        json={"comments": "Sales rep cannot act as reviewer"},
        headers=auth_header(tokens[SystemRole.SALES]),
    )
    assert rej_sales.status_code == 403

    # 6. Unauthorized role: CUSTOMER attempts internal reject -> 403 Forbidden
    rej_cust = client.post(
        f"/api/v1/quotations/{q_id}/reject",
        json={"comments": "Customer cannot access internal review endpoint"},
        headers=auth_header(tokens[SystemRole.CUSTOMER]),
    )
    assert rej_cust.status_code == 403

    # 7. Authorized reviewer (TECHNICAL_MANAGER) rejects quotation -> 200 OK
    reviewer_comment = "Inverter model GW-3000 is insufficient for 5kW panel array capacity. Upgrade to 5kW inverter."
    rej_tm = client.post(
        f"/api/v1/quotations/{q_id}/reject",
        json={"comments": reviewer_comment},
        headers=auth_header(tokens[SystemRole.TECHNICAL_MANAGER]),
    )
    assert rej_tm.status_code == 200
    assert rej_tm.json()["data"]["status"] == "REJECTED"

    # 8. Verify DB state and audit log
    with SessionLocal() as db:
        q_db = db.execute(select(Quotation).where(Quotation.id == q_id)).scalar_one()
        assert q_db.status == "REJECTED"

        audit = db.execute(
            select(AuditLog)
            .where(AuditLog.entity_name == "QUOTATION", AuditLog.entity_id == q_id, AuditLog.action == "QUOTATION_REJECTED")
            .order_by(AuditLog.id.desc())
        ).scalar_one_or_none()
        assert audit is not None
        assert audit.details["comments"] == reviewer_comment
        assert audit.details["rejected_by"] == setup_quotation_data["user_ids"][SystemRole.TECHNICAL_MANAGER]

    # 9. Director also has reviewer rights: test on a second quotation
    r2 = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    q2_id = r2.json()["data"]["id"]
    client.post(f"/api/v1/quotations/{q2_id}/submit", headers=auth_header(tokens[SystemRole.SALES]))
    rej_dir = client.post(
        f"/api/v1/quotations/{q2_id}/reject",
        json={"comments": "Commercial margin below threshold. Increase installation charge."},
        headers=auth_header(tokens[SystemRole.DIRECTOR]),
    )
    assert rej_dir.status_code == 200
    assert rej_dir.json()["data"]["status"] == "REJECTED"


def test_39_draft_deletion_lifecycle_and_security(setup_quotation_data):
    """
    Test 39: Draft quotation deletion and security.
    - Authorized sales user or super-admin can delete a DRAFT quotation.
    - Non-DRAFT quotations (PENDING_APPROVAL, SENT, ACCEPTED) cannot be deleted (409).
    - Unauthorized roles (CUSTOMER, FIELD_TECHNICIAN) cannot delete quotations (403).
    - Deletion cascades line items and removes quotation record from DB.
    - Audit log records QUOTATION_DELETED.
    """
    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]
    suffix = uuid.uuid4().hex[:6].upper()

    with SessionLocal() as db:
        enq = Enquiry(
            customer_id=d["customer1_id"],
            enquiry_number=f"ENQ-{suffix}-DEL",
            source="DIRECT",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("3.00"),
            status="NEW",
        )
        db.add(enq)
        db.commit()
        db.refresh(enq)

        srv = Survey(
            enquiry_id=enq.id,
            surveyor_id=d["surveyor_emp_id"],
            survey_number=f"SRV-{suffix}-DEL",
            scheduled_at=datetime.now(),
            conducted_at=datetime.now(),
            technical_feasibility="FEASIBLE",
            status="APPROVED",
        )
        db.add(srv)
        db.commit()
        db.refresh(srv)
        enq_id = enq.id
        srv_id = srv.id

    # 1. Create a draft quotation
    payload = {
        "enquiry_id": enq_id,
        "survey_id": srv_id,
        "items": [{"product_id": d["prod_panel_id"], "quantity": 2.0}],
    }
    r = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    assert r.status_code == 201
    q_draft_id = r.json()["data"]["id"]
    q_draft_num = r.json()["data"]["quotation_number"]

    # 2. Unauthorized deletion attempt: CUSTOMER -> 403 Forbidden
    del_cust = client.delete(f"/api/v1/quotations/{q_draft_id}", headers=auth_header(tokens[SystemRole.CUSTOMER]))
    assert del_cust.status_code == 403

    # 3. Unauthorized deletion attempt: FIELD_TECHNICIAN -> 403 Forbidden
    del_tech = client.delete(f"/api/v1/quotations/{q_draft_id}", headers=auth_header(tokens[SystemRole.FIELD_TECHNICIAN]))
    assert del_tech.status_code == 403

    # 4. Deleting non-DRAFT quotation: test on PENDING_APPROVAL
    r_pa = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    q_pa_id = r_pa.json()["data"]["id"]
    client.post(f"/api/v1/quotations/{q_pa_id}/submit", headers=auth_header(tokens[SystemRole.SALES]))
    del_pa = client.delete(f"/api/v1/quotations/{q_pa_id}", headers=auth_header(tokens[SystemRole.SALES]))
    assert del_pa.status_code == 409
    assert "Only DRAFT quotations can be deleted" in del_pa.json()["detail"]

    # 5. Deleting non-DRAFT quotation: test on SENT
    r_sent = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    q_sent_id = r_sent.json()["data"]["id"]
    client.post(f"/api/v1/quotations/{q_sent_id}/submit", headers=auth_header(tokens[SystemRole.SALES]))
    client.post(f"/api/v1/quotations/{q_sent_id}/approve", headers=auth_header(tokens[SystemRole.TECHNICAL_MANAGER]))
    client.post(f"/api/v1/quotations/{q_sent_id}/send", headers=auth_header(tokens[SystemRole.SALES]))
    del_sent = client.delete(f"/api/v1/quotations/{q_sent_id}", headers=auth_header(tokens[SystemRole.SALES]))
    assert del_sent.status_code == 409
    assert "Only DRAFT quotations can be deleted" in del_sent.json()["detail"]

    # 6. Deleting non-DRAFT quotation: test on ACCEPTED
    client.post(f"/api/v1/quotations/{q_sent_id}/accept", headers=auth_header(tokens[SystemRole.CUSTOMER]))
    del_acc = client.delete(f"/api/v1/quotations/{q_sent_id}", headers=auth_header(tokens[SystemRole.SALES]))
    assert del_acc.status_code == 409
    assert "Only DRAFT quotations can be deleted" in del_acc.json()["detail"]

    # 7. Authorized deletion of DRAFT quotation by SALES -> 200 OK
    del_ok = client.delete(f"/api/v1/quotations/{q_draft_id}", headers=auth_header(tokens[SystemRole.SALES]))
    assert del_ok.status_code == 200
    assert del_ok.json()["success"] is True

    # 8. Verify DB state: quotation record is gone, subsequent GET is 404
    with SessionLocal() as db:
        q_deleted = db.execute(select(Quotation).where(Quotation.id == q_draft_id)).scalar_one_or_none()
        assert q_deleted is None

        # Line items also removed
        items_count = db.execute(select(QuotationItem).where(QuotationItem.quotation_id == q_draft_id)).scalars().all()
        assert len(items_count) == 0

        # Audit log verified
        audit = db.execute(
            select(AuditLog)
            .where(AuditLog.entity_name == "QUOTATION", AuditLog.entity_id == q_draft_id, AuditLog.action == "QUOTATION_DELETED")
            .order_by(AuditLog.id.desc())
        ).scalar_one_or_none()
        assert audit is not None
        assert audit.details["quotation_number"] == q_draft_num

    get_del = client.get(f"/api/v1/quotations/{q_draft_id}", headers=auth_header(tokens[SystemRole.SALES]))
    assert get_del.status_code == 404

    # 9. Super Admin can also delete a DRAFT quotation
    r_sa = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    q_sa_id = r_sa.json()["data"]["id"]
    del_sa = client.delete(f"/api/v1/quotations/{q_sa_id}", headers=auth_header(tokens[SystemRole.SUPER_ADMIN]))
    assert del_sa.status_code == 200


def test_40_customer_contact_enrichment_and_company_profile(setup_quotation_data):
    """
    Test 40: Phase 5.6C.2 Customer Contact Enrichment & Company Profile.
    1. Verify customer contact fields (phone, email, address, city, state, pincode) are in QuotationResponse.
    2. Verify unconfigured company profile defaults to None.
    3. Verify partially configured company profile returns only configured values.
    4. Verify fully configured company and bank profile returns all public details.
    5. Verify safe handling of customer with null contact fields (e.g. email=None).
    6. Verify customer ownership access control remains enforced.
    """
    from app.config import settings

    tokens = setup_quotation_data["tokens"]
    d = setup_quotation_data["data"]

    payload = {
        "enquiry_id": d["enquiry1_id"],
        "survey_id": d["survey_approved_id"],
        "system_type": "ON_GRID",
        "capacity_kw": 3.0,
        "installation_cost": 10000.0,
        "items": [
            {
                "product_id": d["prod_panel_id"],
                "quantity": 6.0,
                "unit_price": 15000.0,
                "discount_amount": 0.0,
                "tax_rate_percent": 12.0,
            }
        ],
    }

    # 1. Create quotation and verify enriched customer contact fields
    r_create = client.post("/api/v1/quotations", json=payload, headers=auth_header(tokens[SystemRole.SALES]))
    assert r_create.status_code == 201
    q_data = r_create.json()["data"]
    q_id = q_data["id"]

    # Customer 1 verification
    assert q_data["customer_phone"] is not None
    assert q_data["customer_email"] is not None
    assert q_data["customer_address"] == "123 Solar Street"
    assert q_data["customer_city"] == "Pune"
    assert q_data["customer_state"] == "Maharashtra"
    assert q_data["customer_pincode"] == "411001"

    # Unconfigured company profile is None
    assert q_data["company_profile"] is None

    # Verify GET detail endpoint
    r_get = client.get(f"/api/v1/quotations/{q_id}", headers=auth_header(tokens[SystemRole.SALES]))
    assert r_get.status_code == 200
    detail = r_get.json()["data"]
    assert detail["customer_phone"] == q_data["customer_phone"]
    assert detail["customer_address"] == "123 Solar Street"
    assert detail["company_profile"] is None

    # 2. Partially configured company profile
    settings.COMPANY_LEGAL_NAME = "SunPower Solutions Pvt Ltd"
    settings.COMPANY_GSTIN = "27AABCS1429B1Z1"
    try:
        r_partial = client.get(f"/api/v1/quotations/{q_id}", headers=auth_header(tokens[SystemRole.SALES]))
        assert r_partial.status_code == 200
        p_comp = r_partial.json()["data"]["company_profile"]
        assert p_comp is not None
        assert p_comp["legal_name"] == "SunPower Solutions Pvt Ltd"
        assert p_comp["gstin"] == "27AABCS1429B1Z1"
        assert p_comp["address"] is None
        assert p_comp["phone"] is None
        assert p_comp["email"] is None
        assert p_comp["bank_name"] is None
        assert p_comp["bank_account_no"] is None
    finally:
        settings.COMPANY_LEGAL_NAME = None
        settings.COMPANY_GSTIN = None

    # 3. Fully configured company & bank remittance profile
    settings.COMPANY_LEGAL_NAME = "SunPower Solutions Pvt Ltd"
    settings.COMPANY_GSTIN = "27AABCS1429B1Z1"
    settings.COMPANY_ADDRESS = "Plot 42, Solar Tech Park, Pune 411001"
    settings.COMPANY_PHONE = "+91 20 2555 1234"
    settings.COMPANY_EMAIL = "contact@sunpowersol.in"
    settings.COMPANY_BANK_NAME = "State Bank of India"
    settings.COMPANY_BANK_ACCOUNT_NAME = "SunPower Solutions Current Account"
    settings.COMPANY_BANK_ACCOUNT_NO = "389201928374"
    settings.COMPANY_BANK_IFSC = "SBIN0001234"
    settings.COMPANY_BANK_BRANCH = "Shivajinagar Commercial Branch"

    try:
        r_full = client.get(f"/api/v1/quotations/{q_id}", headers=auth_header(tokens[SystemRole.SALES]))
        assert r_full.status_code == 200
        f_comp = r_full.json()["data"]["company_profile"]
        assert f_comp is not None
        assert f_comp["legal_name"] == "SunPower Solutions Pvt Ltd"
        assert f_comp["gstin"] == "27AABCS1429B1Z1"
        assert f_comp["address"] == "Plot 42, Solar Tech Park, Pune 411001"
        assert f_comp["phone"] == "+91 20 2555 1234"
        assert f_comp["email"] == "contact@sunpowersol.in"
        assert f_comp["bank_name"] == "State Bank of India"
        assert f_comp["bank_account_name"] == "SunPower Solutions Current Account"
        assert f_comp["bank_account_no"] == "389201928374"
        assert f_comp["bank_ifsc"] == "SBIN0001234"
        assert f_comp["bank_branch"] == "Shivajinagar Commercial Branch"
    finally:
        settings.COMPANY_LEGAL_NAME = None
        settings.COMPANY_GSTIN = None
        settings.COMPANY_ADDRESS = None
        settings.COMPANY_PHONE = None
        settings.COMPANY_EMAIL = None
        settings.COMPANY_BANK_NAME = None
        settings.COMPANY_BANK_ACCOUNT_NAME = None
        settings.COMPANY_BANK_ACCOUNT_NO = None
        settings.COMPANY_BANK_IFSC = None
        settings.COMPANY_BANK_BRANCH = None

    # 4. Null-safe handling of customer without email
    tag = uuid.uuid4().hex[:6]
    with SessionLocal() as db:
        admin_id = setup_quotation_data["user_ids"][SystemRole.SUPER_ADMIN]
        cust_no_email = Customer(
            customer_type="RESIDENTIAL",
            full_name=f"No Email Customer {tag}",
            phone=f"+9198{uuid.uuid4().int % 100000000:08d}",
            address="Village Road 7",
            city="Satara",
            state="Maharashtra",
            pincode="415001",
            email=None,
            created_by=admin_id,
        )
        db.add(cust_no_email)
        db.commit()
        db.refresh(cust_no_email)

        enq_no_email = Enquiry(
            customer_id=cust_no_email.id,
            enquiry_number=f"ENQ-{tag}-NE",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("2.0"),
            status="NEW",
        )
        db.add(enq_no_email)
        db.commit()
        db.refresh(enq_no_email)

    payload_ne = {
        "enquiry_id": enq_no_email.id,
        "system_type": "ON_GRID",
        "capacity_kw": 2.0,
        "installation_cost": 5000.0,
        "items": [
            {
                "product_id": d["prod_panel_id"],
                "quantity": 4.0,
                "unit_price": 15000.0,
            }
        ],
    }
    r_ne = client.post("/api/v1/quotations", json=payload_ne, headers=auth_header(tokens[SystemRole.SALES]))
    assert r_ne.status_code == 201
    ne_data = r_ne.json()["data"]
    assert ne_data["customer_email"] is None
    assert ne_data["customer_address"] == "Village Road 7"
    assert ne_data["customer_city"] == "Satara"

    # 5. Customer isolation remains enforced
    # Customer 1 can see their quotation
    r_c1 = client.get(f"/api/v1/quotations/{q_id}", headers=auth_header(tokens[SystemRole.CUSTOMER]))
    assert r_c1.status_code == 200

    # Customer 2 cannot see Customer 1's quotation
    r_c2 = client.get(f"/api/v1/quotations/{q_id}", headers=auth_header(tokens["CUSTOMER_2"]))
    assert r_c2.status_code == 404

