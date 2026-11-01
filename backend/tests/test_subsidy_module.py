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
from app.models.projects import Order, Project
from app.models.subsidy import (
    SubsidyApplication,
    SubsidyDocument,
    SubsidyStatusHistory,
    SubsidyPayment,
)
from app.utils.roles import SystemRole
from app.utils.security import hash_password, create_access_token

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_subsidy_env():
    tokens = {}
    user_ids = {}

    with SessionLocal() as db:
        role_slugs = [
            SystemRole.SUPER_ADMIN,
            SystemRole.DIRECTOR,
            SystemRole.TECHNICAL_MANAGER,
            SystemRole.SERVICE_WARRANTY,
            SystemRole.SALES,
            SystemRole.CUSTOMER,
        ]
        for slug in role_slugs:
            role = db.execute(select(Role).where(Role.slug == slug)).scalar_one_or_none()
            if not role:
                role = Role(name=slug.replace("_", " ").title(), slug=slug)
                db.add(role)
                db.flush()

            test_email = f"test_{slug.lower()}_sub@sunpowersol.test"
            user = db.execute(select(User).where(User.email == test_email)).scalar_one_or_none()
            if not user:
                user = User(
                    email=test_email,
                    hashed_password=hash_password("TestSecret123!"),
                    full_name=f"Test {slug} Sub",
                    role_id=role.id,
                    is_active=True,
                )
                db.add(user)
                db.flush()

            tokens[slug] = create_access_token(data={"sub": str(user.id), "role": slug, "email": user.email})
            user_ids[slug] = user.id

        uid = uuid.uuid4().hex[:6]

        # Customer
        cust = db.execute(select(Customer).where(Customer.user_id == user_ids[SystemRole.CUSTOMER])).scalar_one_or_none()
        if not cust:
            cust = Customer(
                user_id=user_ids[SystemRole.CUSTOMER],
                customer_type="INDIVIDUAL",
                full_name=f"Subsidy Beneficiary {uid}",
                phone=f"95{uid[:8]}",
                email=f"sub_client_{uid}@test.com",
                address="12 Green Valley, Pune",
                city="Pune",
                state="Maharashtra",
                pincode="411038",
                created_by=user_ids[SystemRole.SALES],
                is_active=True,
            )
            db.add(cust)
            db.flush()

        # Product
        prod = Product(
            product_code=f"PAN-550-SUB-{uid.upper()}",
            name=f"Mono PERC Bifacial Solar Panel 550W {uid}",
            category="PANELS",
            unit_of_measure="NOS",
            brand="Tata Power Solar",
            wattage_or_capacity="550W",
            base_price=Decimal("15000.00"),
            tax_rate_percent=Decimal("12.00"),
            min_stock_alert=Decimal("10.00"),
            is_serialized=False,
            is_active=True,
        )
        db.add(prod)
        db.flush()

        # Order & Projects: One 5kW system, one 2kW system
        enq = Enquiry(
            enquiry_number=f"ENQ-SUB-{uid.upper()}",
            customer_id=cust.id,
            source="WEBSITE",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("5.00"),
            status="WON",
        )
        db.add(enq)
        db.flush()

        quo = Quotation(
            quotation_number=f"QT-SUB-{uid.upper()}",
            enquiry_id=enq.id,
            version=1,
            system_type="ON_GRID",
            capacity_kw=Decimal("5.00"),
            total_product_cost=Decimal("200000.00"),
            installation_cost=Decimal("20000.00"),
            tax_amount=Decimal("26400.00"),
            gross_amount=Decimal("246400.00"),
            subsidy_estimate=Decimal("78000.00"),
            net_payable_amount=Decimal("168400.00"),
            valid_until=date.today() + timedelta(days=30),
            quotation_date=date.today(),
            status="ACCEPTED",
            created_by=user_ids[SystemRole.SALES],
        )
        db.add(quo)
        db.flush()

        order = Order(
            quotation_id=quo.id,
            customer_id=cust.id,
            order_number=f"ORD-SUB-{uid.upper()}",
            order_date=date.today(),
            status="CONFIRMED",
            total_amount=Decimal("246400.00"),
            advance_paid=Decimal("50000.00"),
            balance_amount=Decimal("196400.00"),
            created_by=user_ids[SystemRole.SALES],
        )
        db.add(order)
        db.flush()

        project_5kw = Project(
            order_id=order.id,
            customer_id=cust.id,
            project_code=f"PRJ-SUB-5K-{uid.upper()}",
            system_capacity_kw=Decimal("5.00"),
            system_type="ON_GRID",
            site_address="12 Green Valley, Pune",
            planned_start_date=date.today() - timedelta(days=20),
            planned_completion_date=date.today(),
            status="COMMISSIONED",
        )
        db.add(project_5kw)
        db.flush()

        db.commit()

        env_data = {
            "tokens": tokens,
            "user_ids": user_ids,
            "project_id": project_5kw.id,
            "customer_id": cust.id,
            "order_id": order.id,
            "quotation_id": quo.id,
            "uid": uid,
        }

    return env_data


def test_subsidy_application_creation_and_auto_slab(setup_subsidy_env):
    data = setup_subsidy_env
    mgr_token = data["tokens"][SystemRole.TECHNICAL_MANAGER]
    project_id = data["project_id"]
    uid = data["uid"]
    headers = {"Authorization": f"Bearer {mgr_token}"}

    # Create application without passing eligible_subsidy_amount for 5kW system
    # Auto-calculated PM Surya Ghar standard slab for 5kW should be max ₹78,000
    payload = {
        "project_id": project_id,
        "portal_registration_number": f"PMSG-{uid.upper()}-001",
        "discom_name": "MSEDCL (Maharashtra State Electricity Distribution)",
        "sanctioned_capacity_kw": "5.00",
        "application_date": str(date.today()),
    }

    resp = client.post("/api/v1/subsidy/applications", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()["data"]

    assert body["application_number"].startswith("SUB-")
    assert body["discom_name"] == payload["discom_name"]
    assert float(body["sanctioned_capacity_kw"]) == 5.00
    assert float(body["eligible_subsidy_amount"]) == 78000.00
    assert body["status"] == "DRAFT"

    # Duplicate project application rejection
    dup = client.post("/api/v1/subsidy/applications", json=payload, headers=headers)
    assert dup.status_code == 400
    assert "already exists for this project" in dup.json()["detail"].lower()


def test_subsidy_status_transitions_and_history(setup_subsidy_env):
    data = setup_subsidy_env
    mgr_token = data["tokens"][SystemRole.TECHNICAL_MANAGER]
    project_id = data["project_id"]
    headers = {"Authorization": f"Bearer {mgr_token}"}

    # Fetch existing application
    app_list = client.get(f"/api/v1/subsidy/applications?project_id={project_id}", headers=headers)
    assert app_list.status_code == 200
    app_id = app_list.json()["data"]["items"][0]["id"]

    # Transition to SUBMITTED_TO_DISCOM
    t1 = client.patch(
        f"/api/v1/subsidy/applications/{app_id}/status",
        json={"status": "SUBMITTED_TO_DISCOM", "comments": "Submitted to MSEDCL portal with all consumer documents."},
        headers=headers,
    )
    assert t1.status_code == 200, t1.text
    assert t1.json()["data"]["status"] == "SUBMITTED_TO_DISCOM"

    # Transition to INSPECTION_SCHEDULED
    t2 = client.patch(
        f"/api/v1/subsidy/applications/{app_id}/status",
        json={"status": "INSPECTION_SCHEDULED", "comments": "DISCOM junior engineer scheduled joint site inspection."},
        headers=headers,
    )
    assert t2.status_code == 200
    assert t2.json()["data"]["status"] == "INSPECTION_SCHEDULED"

    # Transition to APPROVED
    t3 = client.patch(
        f"/api/v1/subsidy/applications/{app_id}/status",
        json={"status": "APPROVED", "comments": "Net meter installed and joint inspection report signed."},
        headers=headers,
    )
    assert t3.status_code == 200
    assert t3.json()["data"]["status"] == "APPROVED"

    # Check detail view history trail
    det = client.get(f"/api/v1/subsidy/applications/{app_id}", headers=headers)
    assert det.status_code == 200
    history = det.json()["data"]["history"]
    assert len(history) >= 4  # DRAFT, SUBMITTED_TO_DISCOM, INSPECTION_SCHEDULED, APPROVED


def test_subsidy_documents_upload_and_verification(setup_subsidy_env):
    data = setup_subsidy_env
    mgr_token = data["tokens"][SystemRole.TECHNICAL_MANAGER]
    cust_token = data["tokens"][SystemRole.CUSTOMER]
    project_id = data["project_id"]

    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # Fetch app
    app_list = client.get(f"/api/v1/subsidy/applications?project_id={project_id}", headers=cust_headers)
    app_id = app_list.json()["data"]["items"][0]["id"]

    # Customer uploads electricity bill
    doc_payload = {
        "document_type": "ELECTRICITY_BILL",
        "file_name": "Latest_MSEDCL_Bill_Oct2026.pdf",
        "remarks": "Electricity consumer bill showing consumer no. 02154879632",
    }
    u_resp = client.post(f"/api/v1/subsidy/applications/{app_id}/documents", json=doc_payload, headers=cust_headers)
    assert u_resp.status_code == 201, u_resp.text
    doc = u_resp.json()["data"]
    doc_id = doc["id"]
    assert doc["document_type"] == "ELECTRICITY_BILL"
    assert doc["verification_status"] == "PENDING"

    # Manager verifies document
    v_resp = client.patch(
        f"/api/v1/subsidy/documents/{doc_id}/verify",
        json={"verification_status": "VERIFIED", "remarks": "Consumer number and sanctioned load verified against DISCOM database."},
        headers=mgr_headers,
    )
    assert v_resp.status_code == 200, v_resp.text
    assert v_resp.json()["data"]["verification_status"] == "VERIFIED"


def test_subsidy_disbursement_recording(setup_subsidy_env):
    data = setup_subsidy_env
    mgr_token = data["tokens"][SystemRole.TECHNICAL_MANAGER]
    project_id = data["project_id"]
    uid = data["uid"]
    headers = {"Authorization": f"Bearer {mgr_token}"}

    app_list = client.get(f"/api/v1/subsidy/applications?project_id={project_id}", headers=headers)
    app_id = app_list.json()["data"]["items"][0]["id"]

    # Record direct benefit transfer disbursement
    pay_payload = {
        "disbursement_date": str(date.today()),
        "disbursed_amount": "78000.00",
        "bank_reference_number": f"DBT-PMSG-{uid.upper()}",
        "payment_reference": f"SUBPAY-REC-{uid.upper()}",
    }

    d_resp = client.post(f"/api/v1/subsidy/applications/{app_id}/disbursements", json=pay_payload, headers=headers)
    assert d_resp.status_code == 201, d_resp.text
    pay = d_resp.json()["data"]
    assert float(pay["disbursed_amount"]) == 78000.00

    # Application status should be updated to SUBSIDY_DISBURSED
    app_check = client.get(f"/api/v1/subsidy/applications/{app_id}", headers=headers)
    assert app_check.json()["data"]["status"] == "SUBSIDY_DISBURSED"


def test_subsidy_customer_isolation_and_rbac(setup_subsidy_env):
    data = setup_subsidy_env
    cust_token = data["tokens"][SystemRole.CUSTOMER]
    sales_token = data["tokens"][SystemRole.SALES]
    project_id = data["project_id"]

    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    sales_headers = {"Authorization": f"Bearer {sales_token}"}

    # Customer can access their own application list
    c_list = client.get("/api/v1/subsidy/applications", headers=cust_headers)
    assert c_list.status_code == 200
    assert len(c_list.json()["data"]["items"]) >= 1

    app_id = c_list.json()["data"]["items"][0]["id"]

    # Customer blocked from directly updating status or recording disbursements
    r1 = client.patch(
        f"/api/v1/subsidy/applications/{app_id}/status",
        json={"status": "APPROVED"},
        headers=cust_headers,
    )
    assert r1.status_code == 403

    # Sales executive blocked from recording subsidy disbursements
    r2 = client.post(
        f"/api/v1/subsidy/applications/{app_id}/disbursements",
        json={"disbursed_amount": "50000.00"},
        headers=sales_headers,
    )
    assert r2.status_code == 403


def test_subsidy_slab_calculations_unit():
    """
    Verify strict Decimal calculations of PM Surya Ghar national slabs across:
    <= 0 kW, 1 kW, 2 kW, 2.5 kW (pro-rata), 3 kW, and > 3 kW capped.
    """
    from app.routers.subsidy import _calculate_standard_subsidy

    # Zero and negative capacity
    assert _calculate_standard_subsidy(Decimal("0.00")) == Decimal("0.00")
    assert _calculate_standard_subsidy(Decimal("-1.50")) == Decimal("0.00")

    # 1 kW -> ₹30,000
    assert _calculate_standard_subsidy(Decimal("1.00")) == Decimal("30000.00")

    # 2 kW -> ₹60,000
    assert _calculate_standard_subsidy(Decimal("2.00")) == Decimal("60000.00")

    # 2.5 kW -> ₹69,000 (₹60,000 + 0.5 * ₹18,000)
    assert _calculate_standard_subsidy(Decimal("2.50")) == Decimal("69000.00")

    # 3 kW -> ₹78,000
    assert _calculate_standard_subsidy(Decimal("3.00")) == Decimal("78000.00")

    # Above 3 kW (e.g. 5 kW, 10 kW) -> Capped strictly at ₹78,000
    assert _calculate_standard_subsidy(Decimal("5.00")) == Decimal("78000.00")
    assert _calculate_standard_subsidy(Decimal("10.00")) == Decimal("78000.00")


def _create_test_order_and_project(db, customer, uid_sub, capacity_kw, sales_user_id):
    enq = Enquiry(
        enquiry_number=f"ENQ-{uid_sub.upper()}",
        customer_id=customer.id,
        source="WEBSITE",
        system_type="ON_GRID",
        proposed_capacity_kw=capacity_kw,
        status="WON",
    )
    db.add(enq)
    db.flush()

    quo = Quotation(
        quotation_number=f"QT-{uid_sub.upper()}",
        enquiry_id=enq.id,
        version=1,
        system_type="ON_GRID",
        capacity_kw=capacity_kw,
        total_product_cost=capacity_kw * Decimal("40000.00"),
        installation_cost=Decimal("15000.00"),
        tax_amount=Decimal("10000.00"),
        gross_amount=capacity_kw * Decimal("40000.00") + Decimal("25000.00"),
        subsidy_estimate=Decimal("0.00"),
        net_payable_amount=capacity_kw * Decimal("40000.00") + Decimal("25000.00"),
        valid_until=date.today() + timedelta(days=30),
        quotation_date=date.today(),
        status="ACCEPTED",
        created_by=sales_user_id,
    )
    db.add(quo)
    db.flush()

    order = Order(
        order_number=f"ORD-{uid_sub.upper()}",
        quotation_id=quo.id,
        customer_id=customer.id,
        order_date=date.today(),
        status="CONFIRMED",
        total_amount=quo.gross_amount,
        advance_paid=Decimal("20000.00"),
        balance_amount=quo.gross_amount - Decimal("20000.00"),
        created_by=sales_user_id,
    )
    db.add(order)
    db.flush()

    proj = Project(
        order_id=order.id,
        customer_id=customer.id,
        project_code=f"PRJ-{uid_sub.upper()}",
        system_capacity_kw=capacity_kw,
        system_type="ON_GRID",
        site_address=customer.address,
        planned_start_date=date.today(),
        planned_completion_date=date.today() + timedelta(days=30),
        status="COMMISSIONED",
    )
    db.add(proj)
    db.flush()
    return proj


def test_commercial_and_industrial_subsidy_rejection(setup_subsidy_env):
    """
    Verify that PM Surya Ghar subsidy applications are rejected for Commercial and Industrial customers.
    """
    data = setup_subsidy_env
    mgr_token = data["tokens"][SystemRole.TECHNICAL_MANAGER]
    sales_uid = data["user_ids"][SystemRole.SALES]
    headers = {"Authorization": f"Bearer {mgr_token}"}
    uid = uuid.uuid4().hex[:6]

    with SessionLocal() as db:
        # Commercial Customer & Project
        comm_cust = Customer(
            customer_type="COMMERCIAL",
            full_name=f"Commercial Logistics {uid}",
            phone=f"91{uid[:8]}",
            email=f"comm_{uid}@test.com",
            address="Plot 5, MIDC Industrial Area, Pune",
            city="Pune",
            state="Maharashtra",
            pincode="411019",
            created_by=sales_uid,
            is_active=True,
        )
        db.add(comm_cust)
        db.flush()
        comm_proj = _create_test_order_and_project(db, comm_cust, f"C{uid}", Decimal("10.00"), sales_uid)

        # Industrial Customer & Project
        ind_cust = Customer(
            customer_type="INDUSTRIAL",
            full_name=f"Industrial Foundry {uid}",
            phone=f"92{uid[:8]}",
            email=f"ind_{uid}@test.com",
            address="Plot 18, Chakan Industrial Estate, Pune",
            city="Pune",
            state="Maharashtra",
            pincode="410501",
            created_by=sales_uid,
            is_active=True,
        )
        db.add(ind_cust)
        db.flush()
        ind_proj = _create_test_order_and_project(db, ind_cust, f"I{uid}", Decimal("50.00"), sales_uid)

        db.commit()
        comm_proj_id = comm_proj.id
        ind_proj_id = ind_proj.id

    # 1. Commercial customer application attempt -> must reject with 400
    res_comm = client.post(
        "/api/v1/subsidy/applications",
        headers=headers,
        json={
            "project_id": comm_proj_id,
            "portal_registration_number": f"PMSG-COMM-{uid.upper()}",
            "discom_name": "MSEDCL",
            "sanctioned_capacity_kw": 10.0,
            "application_date": str(date.today()),
        },
    )
    assert res_comm.status_code == 400
    assert "ineligible" in res_comm.json()["detail"].lower()

    # 2. Industrial customer application attempt -> must reject with 400
    res_ind = client.post(
        "/api/v1/subsidy/applications",
        headers=headers,
        json={
            "project_id": ind_proj_id,
            "portal_registration_number": f"PMSG-IND-{uid.upper()}",
            "discom_name": "MSEDCL",
            "sanctioned_capacity_kw": 50.0,
            "application_date": str(date.today()),
        },
    )
    assert res_ind.status_code == 400
    assert "ineligible" in res_ind.json()["detail"].lower()


def test_residential_customer_subsidy_acceptance_with_pro_rata(setup_subsidy_env):
    """
    Verify that an eligible residential customer with a 2.5 kW system receives the exact ₹69,000 subsidy.
    """
    data = setup_subsidy_env
    mgr_token = data["tokens"][SystemRole.TECHNICAL_MANAGER]
    sales_uid = data["user_ids"][SystemRole.SALES]
    headers = {"Authorization": f"Bearer {mgr_token}"}
    uid = uuid.uuid4().hex[:6]

    with SessionLocal() as db:
        res_cust = Customer(
            customer_type="RESIDENTIAL",
            full_name=f"Residential Homeowner {uid}",
            phone=f"93{uid[:8]}",
            email=f"res_{uid}@test.com",
            address="14 Palm Grove, Kothrud, Pune",
            city="Pune",
            state="Maharashtra",
            pincode="411038",
            created_by=sales_uid,
            is_active=True,
        )
        db.add(res_cust)
        db.flush()

        res_proj = _create_test_order_and_project(db, res_cust, f"R{uid}", Decimal("2.50"), sales_uid)
        db.commit()
        res_proj_id = res_proj.id

    res_app = client.post(
        "/api/v1/subsidy/applications",
        headers=headers,
        json={
            "project_id": res_proj_id,
            "portal_registration_number": f"PMSG-RES-{uid.upper()}",
            "discom_name": "MSEDCL",
            "sanctioned_capacity_kw": 2.50,
            "application_date": str(date.today()),
        },
    )
    assert res_app.status_code == 201, res_app.text
    app_data = res_app.json()["data"]
    assert float(app_data["eligible_subsidy_amount"]) == 69000.00
