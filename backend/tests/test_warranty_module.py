import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from decimal import Decimal
from datetime import date, timedelta
import uuid

from app.main import app
from app.database import SessionLocal
from app.models.auth import User, Role, Employee
from app.models.crm import Customer, Product, Enquiry, Quotation
from app.models.projects import Order, Project, ProjectBomItem
from app.models.inventory import Inventory, SerialNumber, SerialNumberHistory, StockMovement
from app.models.warranty import (
    WarrantyPolicy,
    WarrantyRecord,
    WarrantyEvent,
    ServiceTicket,
    ServiceVisit,
    Replacement,
    ServiceTicketConfirmation,
)
from app.utils.roles import SystemRole
from app.utils.security import hash_password, create_access_token

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_warranty_env():
    tokens = {}
    user_ids = {}

    with SessionLocal() as db:
        role_slugs = [
            SystemRole.SUPER_ADMIN,
            SystemRole.DIRECTOR,
            SystemRole.SERVICE_WARRANTY,
            SystemRole.FIELD_TECHNICIAN,
            SystemRole.SALES,
            SystemRole.CUSTOMER,
        ]
        for slug in role_slugs:
            role = db.execute(select(Role).where(Role.slug == slug)).scalar_one_or_none()
            if not role:
                role = Role(name=slug.replace("_", " ").title(), slug=slug)
                db.add(role)
                db.flush()

            test_email = f"test_{slug.lower()}_war@sunpowersol.test"
            user = db.execute(select(User).where(User.email == test_email)).scalar_one_or_none()
            if not user:
                user = User(
                    email=test_email,
                    hashed_password=hash_password("TestSecret123!"),
                    full_name=f"Test {slug} War",
                    role_id=role.id,
                    is_active=True,
                )
                db.add(user)
                db.flush()

            tokens[slug] = create_access_token(data={"sub": str(user.id), "role": slug, "email": user.email})
            user_ids[slug] = user.id

        uid = uuid.uuid4().hex[:6]

        # Technician employee
        tech_emp = db.execute(select(Employee).where(Employee.user_id == user_ids[SystemRole.FIELD_TECHNICIAN])).scalar_one_or_none()
        if not tech_emp:
            tech_emp = Employee(
                user_id=user_ids[SystemRole.FIELD_TECHNICIAN],
                employee_code=f"EMP-T-{uid.upper()}",
                designation="Field Service Engineer",
                department_id=3,
                employment_type="FULL_TIME",
                joining_date=date.today() - timedelta(days=100),
                is_active=True,
            )
            db.add(tech_emp)
            db.flush()

        # Customer
        cust = db.execute(select(Customer).where(Customer.user_id == user_ids[SystemRole.CUSTOMER])).scalar_one_or_none()
        if not cust:
            cust = Customer(
                user_id=user_ids[SystemRole.CUSTOMER],
                customer_type="INDIVIDUAL",
                full_name=f"Warranty Client {uid}",
                phone=f"96{uid[:8]}",
                email=f"client_war_{uid}@test.com",
                address="77 Solar Heights, Bangalore",
                city="Bangalore",
                state="Karnataka",
                pincode="560001",
                created_by=user_ids[SystemRole.SALES],
                is_active=True,
            )
            db.add(cust)
            db.flush()

        # Product
        prod = Product(
            product_code=f"INV-5K-WAR-{uid.upper()}",
            name=f"Solar Inverter 5kW Smart {uid}",
            category="INVERTER",
            unit_of_measure="NOS",
            brand="SolarEdge",
            model_number="SE5000H",
            wattage_or_capacity="5000W",
            base_price=Decimal("65000.00"),
            tax_rate_percent=Decimal("12.00"),
            min_stock_alert=Decimal("2.00"),
            is_serialized=True,
            is_active=True,
        )
        db.add(prod)
        db.flush()

        # Inventory
        inv = Inventory(
            product_id=prod.id,
            warehouse_location="Warehouse A-1",
            quantity_on_hand=Decimal("10.00"),
            reserved_quantity=Decimal("0.00"),
            quantity_available=Decimal("10.00"),
            average_unit_cost=Decimal("55000.00"),
            reorder_level=Decimal("2.00"),
        )
        db.add(inv)
        db.flush()

        # Serial numbers: One installed on project, one in warehouse ready for replacement
        sn_installed = SerialNumber(
            serial_number=f"SN-INST-{uid.upper()}-01",
            product_id=prod.id,
            inventory_id=inv.id,
            status="INSTALLED",
            warranty_months=60,
            received_date=date.today() - timedelta(days=30),
        )
        db.add(sn_installed)

        sn_spare = SerialNumber(
            serial_number=f"SN-SPARE-{uid.upper()}-02",
            product_id=prod.id,
            inventory_id=inv.id,
            status="IN_STOCK",
            warranty_months=60,
            received_date=date.today() - timedelta(days=10),
        )
        db.add(sn_spare)
        db.flush()

        # Order & Project
        enq = Enquiry(
            enquiry_number=f"ENQ-WAR-{uid.upper()}",
            customer_id=cust.id,
            source="DIRECT",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("5.00"),
            status="WON",
        )
        db.add(enq)
        db.flush()

        quo = Quotation(
            quotation_number=f"QT-WAR-{uid.upper()}",
            enquiry_id=enq.id,
            version=1,
            system_type="ON_GRID",
            capacity_kw=Decimal("5.00"),
            total_product_cost=Decimal("180000.00"),
            installation_cost=Decimal("20000.00"),
            tax_amount=Decimal("24000.00"),
            gross_amount=Decimal("224000.00"),
            subsidy_estimate=Decimal("0.00"),
            net_payable_amount=Decimal("224000.00"),
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
            order_number=f"ORD-WAR-{uid.upper()}",
            order_date=date.today(),
            status="CONFIRMED",
            total_amount=Decimal("224000.00"),
            advance_paid=Decimal("50000.00"),
            balance_amount=Decimal("174000.00"),
            created_by=user_ids[SystemRole.SALES],
        )
        db.add(order)
        db.flush()

        project = Project(
            order_id=order.id,
            customer_id=cust.id,
            project_code=f"PRJ-WAR-{uid.upper()}",
            system_capacity_kw=Decimal("5.00"),
            system_type="ON_GRID",
            site_address="77 Solar Heights, Bangalore",
            planned_start_date=date.today() - timedelta(days=15),
            planned_completion_date=date.today(),
            status="COMMISSIONED",
        )
        db.add(project)
        db.flush()

        # Record serial history associating sn_installed with this project
        sn_hist = SerialNumberHistory(
            serial_number_id=sn_installed.id,
            action_taken="INSTALLED",
            previous_status="DISPATCHED",
            new_status="INSTALLED",
            project_id=project.id,
            recorded_by=user_ids[SystemRole.SUPER_ADMIN],
            remarks="Installed and commissioned on site",
        )
        db.add(sn_hist)

        db.commit()

        env_data = {
            "tokens": tokens,
            "user_ids": user_ids,
            "project_id": project.id,
            "customer_id": cust.id,
            "product_id": prod.id,
            "sn_installed_id": sn_installed.id,
            "sn_spare_id": sn_spare.id,
            "tech_emp_id": tech_emp.id,
            "uid": uid,
        }

    return env_data


def test_warranty_policy_creation_and_listing(setup_warranty_env):
    data = setup_warranty_env
    staff_token = data["tokens"][SystemRole.SERVICE_WARRANTY]
    uid = data["uid"]
    headers = {"Authorization": f"Bearer {staff_token}"}

    payload = {
        "policy_code": f"POL-INV-{uid.upper()}",
        "name": f"SolarEdge 10-Year Inverter Policy {uid}",
        "warranty_period_months": 120,
        "activation_trigger": "COMMISSIONING",
        "terms_and_conditions": "100% parts and on-site labor coverage for 10 years.",
    }

    resp = client.post("/api/v1/warranty/policies", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()["data"]
    assert body["policy_code"] == payload["policy_code"]
    assert body["warranty_period_months"] == 120

    # Duplicate code rejection
    dup = client.post("/api/v1/warranty/policies", json=payload, headers=headers)
    assert dup.status_code == 400
    assert "already exists" in dup.json()["detail"].lower()

    # List policies
    list_resp = client.get("/api/v1/warranty/policies", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) >= 1


def test_project_warranty_registration(setup_warranty_env):
    data = setup_warranty_env
    staff_token = data["tokens"][SystemRole.SERVICE_WARRANTY]
    project_id = data["project_id"]
    headers = {"Authorization": f"Bearer {staff_token}"}

    reg_resp = client.post(f"/api/v1/projects/{project_id}/warranty-register", headers=headers)
    assert reg_resp.status_code == 201, reg_resp.text
    records = reg_resp.json()["data"]
    assert len(records) >= 1

    rec = records[0]
    assert rec["status"] == "ACTIVE"
    assert rec["certificate_number"].startswith("CERT-")
    assert rec["warranty_start_date"] == str(date.today())

    # Verify record detail has initial ACTIVATION event
    rec_id = rec["id"]
    det_resp = client.get(f"/api/v1/warranty/records/{rec_id}", headers=headers)
    assert det_resp.status_code == 200
    detail = det_resp.json()["data"]
    assert len(detail["events"]) == 1
    assert detail["events"][0]["event_type"] == "ACTIVATION"


def test_service_ticket_lifecycle_and_visits(setup_warranty_env):
    data = setup_warranty_env
    staff_token = data["tokens"][SystemRole.SERVICE_WARRANTY]
    cust_token = data["tokens"][SystemRole.CUSTOMER]
    project_id = data["project_id"]
    sn_id = data["sn_installed_id"]
    tech_emp_id = data["tech_emp_id"]

    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    # 1. Customer creates ticket for grid tripping
    ticket_payload = {
        "project_id": project_id,
        "serial_number_id": sn_id,
        "issue_category": "INVERTER_FAULT",
        "priority": "HIGH",
        "description": "Inverter displays Error Code 18: Grid Synchronization Trip during noon peak.",
    }
    t_resp = client.post("/api/v1/service-tickets", json=ticket_payload, headers=cust_headers)
    assert t_resp.status_code == 201, t_resp.text
    ticket = t_resp.json()["data"]
    ticket_id = ticket["id"]
    assert ticket["status"] == "OPEN"
    assert ticket["ticket_number"].startswith("TKT-")

    # 2. Staff schedules technician visit
    visit_payload = {
        "technician_id": tech_emp_id,
        "scheduled_date": str(date.today()),
    }
    v_resp = client.post(f"/api/v1/service-tickets/{ticket_id}/visits", json=visit_payload, headers=staff_headers)
    assert v_resp.status_code == 201, v_resp.text
    visit = v_resp.json()["data"]
    visit_id = visit["id"]
    assert visit["visit_status"] == "SCHEDULED"

    # Ticket should now be ASSIGNED
    td_resp = client.get(f"/api/v1/service-tickets/{ticket_id}", headers=staff_headers)
    assert td_resp.json()["data"]["status"] == "ASSIGNED"

    # 3. Technician completes visit
    comp_payload = {
        "findings": "Internal DC-AC IGBT bridge defective due to transient surge.",
        "action_taken": "Isolator tripped. Requires warranty unit swap.",
        "parts_replaced": True,
        "customer_present_name": "R. Sharma",
    }
    comp_resp = client.patch(f"/api/v1/service-visits/{visit_id}/complete", json=comp_payload, headers=staff_headers)
    assert comp_resp.status_code == 200, comp_resp.text
    assert comp_resp.json()["data"]["visit_status"] == "COMPLETED"


def test_component_replacement_under_warranty(setup_warranty_env):
    data = setup_warranty_env
    staff_token = data["tokens"][SystemRole.SERVICE_WARRANTY]
    project_id = data["project_id"]
    sn_orig_id = data["sn_installed_id"]
    sn_spare_id = data["sn_spare_id"]
    headers = {"Authorization": f"Bearer {staff_token}"}

    # Fetch open ticket or create one if running test in isolation
    t_list = client.get(f"/api/v1/service-tickets?project_id={project_id}", headers=headers)
    assert t_list.status_code == 200
    items = t_list.json()["data"]["items"]
    if items:
        ticket_id = items[0]["id"]
    else:
        t_resp = client.post("/api/v1/service-tickets", json={
            "project_id": project_id,
            "serial_number_id": sn_orig_id,
            "issue_category": "INVERTER_FAULT",
            "priority": "HIGH",
            "description": "Inverter fault for replacement test",
        }, headers=headers)
        assert t_resp.status_code == 201
        ticket_id = t_resp.json()["data"]["id"]

    # Swap defective original serial with spare serial
    rep_payload = {
        "original_serial_id": sn_orig_id,
        "replacement_serial_id": sn_spare_id,
        "replacement_reason": "IGBT bridge burnout replaced under standard warranty.",
        "replacement_date": str(date.today()),
    }
    r_resp = client.post(f"/api/v1/service-tickets/{ticket_id}/replacements", json=rep_payload, headers=headers)
    assert r_resp.status_code == 201, r_resp.text
    rep_data = r_resp.json()["data"]
    assert rep_data["original_serial_id"] == sn_orig_id
    assert rep_data["replacement_serial_id"] == sn_spare_id

    # Verify SerialNumber database status and StockMovement ledger
    with SessionLocal() as db:
        orig = db.get(SerialNumber, sn_orig_id)
        spare = db.get(SerialNumber, sn_spare_id)
        assert orig.status == "DEFECTIVE"
        assert spare.status == "INSTALLED"

        # Verify stock movement recorded for warranty replacement
        mov = db.execute(
            select(StockMovement).where(
                StockMovement.reference_type == "SERVICE_TICKET",
                StockMovement.reference_id == ticket_id,
            )
        ).scalar_one_or_none()
        assert mov is not None
        assert mov.movement_type == "ADJUSTMENT"
        assert float(mov.quantity) == -1.00

    # 1. Duplicate replacement retry on same ticket must be rejected (idempotency guard)
    dup_resp = client.post(f"/api/v1/service-tickets/{ticket_id}/replacements", json=rep_payload, headers=headers)
    assert dup_resp.status_code == 400
    assert "already been replaced" in dup_resp.json()["detail"].lower()

    # 2. Replacement with a serial that is not IN_STOCK must be rejected
    bad_serial_payload = {
        "original_serial_id": sn_orig_id,
        "replacement_serial_id": sn_spare_id,  # now INSTALLED, not IN_STOCK
        "replacement_reason": "Attempting to reuse already installed serial",
        "replacement_date": str(date.today()),
    }
    bad_resp = client.post(f"/api/v1/service-tickets/{ticket_id}/replacements", json=bad_serial_payload, headers=headers)
    assert bad_resp.status_code == 400

    # 3. Replacement with incompatible product component must be rejected
    uid = uuid.uuid4().hex[:6]
    with SessionLocal() as db:
        diff_prod = Product(
            product_code=f"PRD-DIFF-{uid.upper()}",
            name=f"Different Product {uid}",
            category="PANELS",
            unit_of_measure="NOS",
            base_price=Decimal("12000.00"),
            tax_rate_percent=Decimal("12.00"),
            is_serialized=True,
            is_active=True,
        )
        db.add(diff_prod)
        db.flush()

        diff_inv = Inventory(
            product_id=diff_prod.id,
            warehouse_location="Warehouse B-2",
            quantity_on_hand=Decimal("5.00"),
            reserved_quantity=Decimal("0.00"),
            quantity_available=Decimal("5.00"),
            average_unit_cost=Decimal("12000.00"),
        )
        db.add(diff_inv)
        db.flush()

        diff_sn = SerialNumber(
            serial_number=f"SN-DIFF-{uid.upper()}",
            product_id=diff_prod.id,
            inventory_id=diff_inv.id,
            status="IN_STOCK",
            warranty_months=36,
            received_date=date.today(),
        )
        db.add(diff_sn)

        orig_sn2 = SerialNumber(
            serial_number=f"SN-INST2-{uid.upper()}",
            product_id=data["product_id"],
            status="INSTALLED",
            warranty_months=60,
            received_date=date.today(),
        )
        db.add(orig_sn2)
        db.commit()
        diff_sn_id = diff_sn.id
        orig_sn2_id = orig_sn2.id

    t2_resp = client.post("/api/v1/service-tickets", json={
        "project_id": project_id,
        "serial_number_id": orig_sn2_id,
        "issue_category": "INVERTER_FAULT",
        "priority": "MEDIUM",
        "description": "Second ticket to test incompatible component replacement",
    }, headers=headers)
    assert t2_resp.status_code == 201
    ticket2_id = t2_resp.json()["data"]["id"]

    incompat_payload = {
        "original_serial_id": orig_sn2_id,
        "replacement_serial_id": diff_sn_id,
        "replacement_reason": "Incompatible product replacement test",
        "replacement_date": str(date.today()),
    }
    incompat_resp = client.post(f"/api/v1/service-tickets/{ticket2_id}/replacements", json=incompat_payload, headers=headers)
    assert incompat_resp.status_code == 400
    assert "product id" in incompat_resp.json()["detail"].lower()


def test_service_ticket_confirmation_and_isolation(setup_warranty_env):
    data = setup_warranty_env
    cust_token = data["tokens"][SystemRole.CUSTOMER]
    sales_token = data["tokens"][SystemRole.SALES]
    project_id = data["project_id"]

    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    sales_headers = {"Authorization": f"Bearer {sales_token}"}

    # Fetch ticket
    t_list = client.get(f"/api/v1/service-tickets?project_id={project_id}", headers=cust_headers)
    ticket_id = t_list.json()["data"]["items"][0]["id"]

    # Customer confirms resolution
    conf_payload = {
        "resolution_confirmed": True,
        "customer_rating": 5,
        "customer_feedback": "Prompt inverter replacement and system is generating peak power again!",
        "confirmation_channel": "PORTAL",
    }
    c_resp = client.post(f"/api/v1/service-tickets/{ticket_id}/confirm", json=conf_payload, headers=cust_headers)
    assert c_resp.status_code == 201, c_resp.text
    conf = c_resp.json()["data"]
    assert conf["resolution_confirmed"] is True
    assert conf["customer_rating"] == 5

    # Ticket is now RESOLVED
    t_detail = client.get(f"/api/v1/service-tickets/{ticket_id}", headers=cust_headers)
    assert t_detail.json()["data"]["status"] == "RESOLVED"

    # Duplicate confirmation prevented
    dup_conf = client.post(f"/api/v1/service-tickets/{ticket_id}/confirm", json=conf_payload, headers=cust_headers)
    assert dup_conf.status_code == 400
    assert "already been confirmed" in dup_conf.json()["detail"].lower()

    # Sales user denied access to staff operations like policy creation
    r_unauth = client.post(
        "/api/v1/warranty/policies",
        json={"policy_code": "POL-UNAUTH", "name": "Fake", "warranty_period_months": 12},
        headers=sales_headers,
    )
    assert r_unauth.status_code == 403
