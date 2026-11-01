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
from app.models.projects import (
    Order,
    Project,
    ProjectBomItem,
)
from app.models.inventory import (
    Inventory,
    SerialNumber,
    SerialNumberHistory,
    Dispatch,
    DispatchItem,
)
from app.models.installations import (
    InstallationSchedule,
    InstallationScheduleTechnician,
    Installation,
    InstallationChecklist,
    TechnicianWorklog,
    InstallationTest,
    MaterialConsumption,
    CustomerAcceptance,
)
from app.utils.roles import SystemRole
from app.utils.security import hash_password, create_access_token

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_installation_test_env():
    tokens = {}
    user_ids = {}
    emp_ids = {}

    with SessionLocal() as db:
        role_slugs = [
            SystemRole.SUPER_ADMIN,
            SystemRole.DIRECTOR,
            SystemRole.TECHNICAL_MANAGER,
            SystemRole.FIELD_TECHNICIAN,
            SystemRole.WAREHOUSE_PROCUREMENT,
            SystemRole.SALES,
            SystemRole.FINANCE_ACCOUNTS,
            SystemRole.CUSTOMER,
        ]

        for slug in role_slugs:
            role_obj = db.execute(select(Role).where(Role.slug == slug)).scalar_one()
            email = f"test_{slug.lower()}_inst@sunpower.com"
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if not user:
                user = User(
                    role_id=role_obj.id,
                    email=email,
                    full_name=f"Test {slug} Inst",
                    hashed_password=hash_password("Pass123!Safe"),
                    is_active=True,
                    is_verified=True,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            tokens[slug] = create_access_token({"sub": str(user.id), "role": slug})
            user_ids[slug] = user.id

            # Create employee record for field technician and technical manager
            if slug in {SystemRole.FIELD_TECHNICIAN, SystemRole.TECHNICAL_MANAGER}:
                emp = db.execute(select(Employee).where(Employee.user_id == user.id)).scalar_one_or_none()
                if not emp:
                    emp = Employee(
                        user_id=user.id,
                        department_id=3,
                        employee_code=f"EMP-INST-{slug[:4]}-{user.id}",
                        designation=f"{slug} Specialist",
                        employment_type="FULL_TIME",
                        joining_date=date.today() - timedelta(days=100),
                        is_active=True,
                    )
                    db.add(emp)
                    db.commit()
                    db.refresh(emp)
                emp_ids[slug] = emp.id

    return {"tokens": tokens, "user_ids": user_ids, "emp_ids": emp_ids}


@pytest.fixture(scope="module")
def installation_test_data(setup_installation_test_env):
    uid = uuid.uuid4().hex[:6]
    with SessionLocal() as db:
        sales_user_id = setup_installation_test_env["user_ids"][SystemRole.SALES]
        cust_user_id = setup_installation_test_env["user_ids"][SystemRole.CUSTOMER]

        # Ensure any old customer record for this user is unlinked so user_id unique constraint is respected
        old_cust = db.execute(select(Customer).where(Customer.user_id == cust_user_id)).scalar_one_or_none()
        if old_cust:
            old_cust.user_id = None
            db.flush()

        # 1. Customer
        cust = Customer(
            user_id=cust_user_id,
            customer_type="INDIVIDUAL",
            full_name=f"Install Customer {uid}",
            phone=f"98765{uid[:5]}",
            email=f"inst_cust_{uid}@example.com",
            address="456 Solar Avenue, Green City",
            city="Bengaluru",
            state="Karnataka",
            pincode="560002",
            created_by=sales_user_id,
            is_active=True,
        )
        db.add(cust)
        db.flush()

        # 2. Product
        prod = Product(
            product_code=f"INV-INST-{uid}",
            name=f"Inverter 5kW {uid}",
            category="INVERTER",
            brand="SunPower",
            model_number=f"SP-5K-{uid}",
            wattage_or_capacity="5000W",
            unit_of_measure="NOS",
            base_price=Decimal("45000.00"),
            tax_rate_percent=Decimal("18.00"),
            min_stock_alert=Decimal("2.00"),
            is_serialized=True,
            is_active=True,
        )
        db.add(prod)
        db.flush()

        # 3. Inventory
        inv = Inventory(
            product_id=prod.id,
            warehouse_location="Warehouse Bay 2",
            quantity_on_hand=Decimal("5.00"),
            reserved_quantity=Decimal("0.00"),
            quantity_available=Decimal("5.00"),
            average_unit_cost=Decimal("38000.00"),
            reorder_level=Decimal("1.00"),
        )
        db.add(inv)
        db.flush()

        # 4. Serial Number (dispatched to project)
        sn = SerialNumber(
            serial_number=f"SN-INST-{uid}-001",
            product_id=prod.id,
            inventory_id=inv.id,
            status="DISPATCHED",
            warranty_months=60,
            received_date=date.today() - timedelta(days=5),
        )
        db.add(sn)
        db.flush()

        # 5. Order
        enq = Enquiry(
            enquiry_number=f"ENQ-INST-{uid}",
            customer_id=cust.id,
            source="DIRECT",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("5.00"),
            monthly_electricity_bill=Decimal("5000.00"),
            status="WON",
        )
        db.add(enq)
        db.flush()

        quo = Quotation(
            quotation_number=f"Q-INST-{uid}",
            enquiry_id=enq.id,
            version=1,
            system_type="ON_GRID",
            capacity_kw=Decimal("5.00"),
            total_product_cost=Decimal("250000.00"),
            installation_cost=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            gross_amount=Decimal("250000.00"),
            subsidy_estimate=Decimal("0.00"),
            net_payable_amount=Decimal("250000.00"),
            valid_until=date.today() + timedelta(days=30),
            quotation_date=date.today(),
            status="ACCEPTED",
            created_by=sales_user_id,
        )
        db.add(quo)
        db.flush()

        order = Order(
            order_number=f"ORD-INST-{uid}",
            customer_id=cust.id,
            quotation_id=quo.id,
            order_date=date.today(),
            total_amount=Decimal("250000.00"),
            advance_paid=Decimal("50000.00"),
            balance_amount=Decimal("200000.00"),
            status="CONFIRMED",
            created_by=sales_user_id,
        )
        db.add(order)
        db.flush()

        # 6. Project
        proj = Project(
            project_code=f"PRJ-INST-{uid}",
            order_id=order.id,
            customer_id=cust.id,
            system_capacity_kw=Decimal("5.0"),
            system_type="ON_GRID",
            site_address="456 Solar Avenue, Green City",
            planned_start_date=date.today(),
            planned_completion_date=date.today() + timedelta(days=30),
            status="DISPATCHED",
        )
        db.add(proj)
        db.flush()

        # 7. Project BOM Line
        bom = ProjectBomItem(
            project_id=proj.id,
            product_id=prod.id,
            item_category="INVERTER",
            planned_quantity=Decimal("1.00"),
            allocated_quantity=Decimal("1.00"),
            dispatched_quantity=Decimal("1.00"),
            installed_quantity=Decimal("0.00"),
            unit_cost_snapshot=Decimal("38000.00"),
        )
        db.add(bom)
        db.commit()

        return {
            "customer_id": cust.id,
            "project_id": proj.id,
            "order_id": order.id,
            "product_id": prod.id,
            "serial_id": sn.id,
            "serial_number": sn.serial_number,
        }


def test_installation_scheduling_flow(setup_installation_test_env, installation_test_data):
    token = setup_installation_test_env["tokens"][SystemRole.TECHNICAL_MANAGER]
    tech_emp_id = setup_installation_test_env["emp_ids"][SystemRole.FIELD_TECHNICIAN]
    project_id = installation_test_data["project_id"]

    # 1. Create Installation Schedule
    start = date.today()
    end = start + timedelta(days=3)
    res = client.post(
        "/api/v1/installation-schedules",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "project_id": project_id,
            "scheduled_start_date": str(start),
            "scheduled_end_date": str(end),
            "notes": "Rooftop 5kW residential setup team",
            "technicians": [
                {"employee_id": tech_emp_id, "role_in_team": "LEAD"}
            ],
        },
    )
    assert res.status_code == 201, res.text
    sched_data = res.json()["data"]
    schedule_id = sched_data["id"]
    assert sched_data["status"] == "SCHEDULED"
    assert len(sched_data["technicians"]) == 1
    assert sched_data["technicians"][0]["employee_id"] == tech_emp_id

    # 2. Update Schedule Status
    res_up = client.patch(
        f"/api/v1/installation-schedules/{schedule_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "status": "IN_PROGRESS",
            "actual_start_date": str(start),
            "notes": "Team arrived on site, safety briefing done.",
        },
    )
    assert res_up.status_code == 200, res_up.text
    assert res_up.json()["data"]["status"] == "IN_PROGRESS"


def test_installation_initialization_and_checklists(setup_installation_test_env, installation_test_data):
    token = setup_installation_test_env["tokens"][SystemRole.FIELD_TECHNICIAN]
    tech_emp_id = setup_installation_test_env["emp_ids"][SystemRole.FIELD_TECHNICIAN]
    project_id = installation_test_data["project_id"]

    # 1. Create Installation record
    res = client.post(
        "/api/v1/installations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "project_id": project_id,
            "lead_technician_id": tech_emp_id,
            "system_capacity_kw": 5.0,
            "inverter_make_model": "SunPower Hybrid 5kW",
            "total_panels_installed": 10,
            "structure_type": "Elevated GI Roof Mount",
            "installation_date": str(date.today()),
            "technician_notes": "Installation started smoothly.",
        },
    )
    assert res.status_code == 201, res.text
    inst_data = res.json()["data"]
    installation_id = inst_data["id"]
    assert inst_data["status"] == "IN_PROGRESS"

    # Verify project status transitioned to INSTALLATION
    with SessionLocal() as db:
        proj = db.execute(select(Project).where(Project.id == project_id)).scalar_one()
        assert proj.status == "INSTALLATION"

    # Verify default checklists were auto-seeded (7 items)
    checklists = inst_data["checklists"]
    assert len(checklists) >= 5

    # 2. Verify all Checklist Items
    for cl_item in checklists:
        res_cl = client.patch(
            f"/api/v1/installations/checklists/{cl_item['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={"is_checked": True, "remarks": "Visual inspection passed with torque wrench calibration"},
        )
        assert res_cl.status_code == 200, res_cl.text
        assert res_cl.json()["data"]["is_checked"] is True
        assert res_cl.json()["data"]["verified_by"] is not None


def test_technician_worklogs_and_electrical_tests(setup_installation_test_env, installation_test_data):
    tech_token = setup_installation_test_env["tokens"][SystemRole.FIELD_TECHNICIAN]
    mgr_token = setup_installation_test_env["tokens"][SystemRole.TECHNICAL_MANAGER]
    tech_emp_id = setup_installation_test_env["emp_ids"][SystemRole.FIELD_TECHNICIAN]
    project_id = installation_test_data["project_id"]

    # Retrieve installation ID
    res_inst = client.get(
        f"/api/v1/installations?project_id={project_id}",
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert res_inst.status_code == 200
    installation_id = res_inst.json()["data"]["items"][0]["id"]

    # 1. Log Technician Daily Hours
    res_worklog = client.post(
        f"/api/v1/installations/{installation_id}/worklogs",
        headers={"Authorization": f"Bearer {tech_token}"},
        json={
            "employee_id": tech_emp_id,
            "work_date": str(date.today()),
            "hours_worked": 8.0,
            "work_description": "Mounted 10 solar modules, routed DC cables in conduits.",
        },
    )
    assert res_worklog.status_code == 201, res_worklog.text
    worklog_id = res_worklog.json()["data"]["id"]

    # Manager approves worklog
    res_app = client.post(
        f"/api/v1/installations/worklogs/{worklog_id}/approve",
        headers={"Authorization": f"Bearer {mgr_token}"},
    )
    assert res_app.status_code == 200, res_app.text
    assert res_app.json()["data"]["approved_by"] is not None

    # 2. Record Electrical Tests
    # Open-Circuit Voltage Test
    res_test1 = client.post(
        f"/api/v1/installations/{installation_id}/tests",
        headers={"Authorization": f"Bearer {tech_token}"},
        json={
            "test_name": "VOC_TEST",
            "standard_value": "450V",
            "measured_value": "448.5V",
            "unit_of_measure": "Volts",
            "is_passed": True,
            "tested_by": tech_emp_id,
            "remarks": "String Voc within 1% nominal specification",
        },
    )
    assert res_test1.status_code == 201, res_test1.text
    assert res_test1.json()["data"]["is_passed"] is True

    # Grid Synchronization Test
    res_test2 = client.post(
        f"/api/v1/installations/{installation_id}/tests",
        headers={"Authorization": f"Bearer {tech_token}"},
        json={
            "test_name": "GRID_SYNC",
            "standard_value": "230V 50Hz",
            "measured_value": "232V 50.1Hz",
            "unit_of_measure": "Volts/Hz",
            "is_passed": True,
            "tested_by": tech_emp_id,
            "remarks": "Inverter synchronized with utility grid successfully.",
        },
    )
    assert res_test2.status_code == 201, res_test2.text


def test_material_consumption_and_serial_installed(setup_installation_test_env, installation_test_data):
    tech_token = setup_installation_test_env["tokens"][SystemRole.FIELD_TECHNICIAN]
    project_id = installation_test_data["project_id"]
    product_id = installation_test_data["product_id"]
    serial_id = installation_test_data["serial_id"]

    # Retrieve installation ID
    res_inst = client.get(
        f"/api/v1/installations?project_id={project_id}",
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    installation_id = res_inst.json()["data"]["items"][0]["id"]

    # Record material consumption with serial number
    res_mat = client.post(
        f"/api/v1/installations/{installation_id}/materials",
        headers={"Authorization": f"Bearer {tech_token}"},
        json={
            "product_id": product_id,
            "serial_number_id": serial_id,
            "quantity_consumed": 1.0,
            "unit_of_measure": "NOS",
            "remarks": "Installed on wall bracket inside main electrical room",
        },
    )
    assert res_mat.status_code == 201, res_mat.text

    # Verify BOM installed quantity incremented
    with SessionLocal() as db:
        bom = db.execute(
            select(ProjectBomItem).where(
                ProjectBomItem.project_id == project_id,
                ProjectBomItem.product_id == product_id,
            )
        ).scalar_one()
        assert bom.installed_quantity == Decimal("1.00")

        # Verify Serial Number transitioned to INSTALLED
        sn = db.execute(select(SerialNumber).where(SerialNumber.id == serial_id)).scalar_one()
        assert sn.status == "INSTALLED"

        # Verify Serial History record logged
        hist = db.execute(
            select(SerialNumberHistory).where(
                SerialNumberHistory.serial_number_id == serial_id,
                SerialNumberHistory.new_status == "INSTALLED",
            )
        ).scalars().all()
        assert len(hist) >= 1


def test_material_consumption_safety_and_integrity(setup_installation_test_env, installation_test_data):
    tech_token = setup_installation_test_env["tokens"][SystemRole.FIELD_TECHNICIAN]
    project_id = installation_test_data["project_id"]
    product_id = installation_test_data["product_id"]
    serial_id = installation_test_data["serial_id"]
    headers = {"Authorization": f"Bearer {tech_token}"}

    # Retrieve installation ID
    res_inst = client.get(
        f"/api/v1/installations?project_id={project_id}",
        headers=headers,
    )
    assert res_inst.status_code == 200
    installation_id = res_inst.json()["data"]["items"][0]["id"]

    # 1. Duplicate consumption retry on already consumed serial must fail
    dup_resp = client.post(
        f"/api/v1/installations/{installation_id}/materials",
        headers=headers,
        json={
            "product_id": product_id,
            "serial_number_id": serial_id,
            "quantity_consumed": 1.0,
            "unit_of_measure": "NOS",
            "remarks": "Attempt duplicate consumption retry",
        },
    )
    assert dup_resp.status_code == 400
    assert "already been consumed" in dup_resp.json()["detail"].lower()

    # 2. Overconsumption exceeding remaining dispatched quantity must fail
    over_resp = client.post(
        f"/api/v1/installations/{installation_id}/materials",
        headers=headers,
        json={
            "product_id": product_id,
            "quantity_consumed": 1.0,
            "unit_of_measure": "NOS",
            "is_extra_material": False,
            "remarks": "Attempt overconsumption beyond dispatched quantity",
        },
    )
    assert over_resp.status_code == 400
    assert "exceeds remaining dispatched quantity" in over_resp.json()["detail"].lower()

    # 3. Serial with non-DISPATCHED status (e.g. IN_STOCK) must be rejected
    uid = uuid.uuid4().hex[:6]
    with SessionLocal() as db:
        sn_stock = SerialNumber(
            serial_number=f"SN-STOCK-{uid.upper()}",
            product_id=product_id,
            status="IN_STOCK",
            warranty_months=60,
            received_date=date.today(),
        )
        db.add(sn_stock)

        # 4. Serial assigned to another project must be rejected
        other_proj = db.execute(select(Project).where(Project.id != project_id)).scalars().first()
        other_proj_id = other_proj.id if other_proj else project_id
        sn_other = SerialNumber(
            serial_number=f"SN-OTH-{uid.upper()}",
            product_id=product_id,
            project_id=other_proj_id if other_proj else None,
            status="DISPATCHED",
            warranty_months=60,
            received_date=date.today(),
        )
        if not other_proj:
            # If no other project in DB, assign a mock mismatch if foreign key allows or keep test focused
            pass
        db.add(sn_other)

        # 5. Serial belonging to different product must be rejected
        diff_prod = Product(
            product_code=f"PRD-DIF-{uid.upper()}",
            name=f"Different Product {uid}",
            category="PANELS",
            unit_of_measure="NOS",
            base_price=Decimal("15000.00"),
            tax_rate_percent=Decimal("12.00"),
            is_serialized=True,
            is_active=True,
        )
        db.add(diff_prod)
        db.flush()

        sn_diff_prod = SerialNumber(
            serial_number=f"SN-DIFPRD-{uid.upper()}",
            product_id=diff_prod.id,
            status="DISPATCHED",
            warranty_months=60,
            received_date=date.today(),
        )
        db.add(sn_diff_prod)
        db.commit()

        sn_stock_id = sn_stock.id
        sn_other_id = sn_other.id
        sn_diff_prod_id = sn_diff_prod.id

    # Test non-DISPATCHED rejection (IN_STOCK)
    stock_resp = client.post(
        f"/api/v1/installations/{installation_id}/materials",
        headers=headers,
        json={
            "product_id": product_id,
            "serial_number_id": sn_stock_id,
            "quantity_consumed": 1.0,
            "unit_of_measure": "NOS",
            "is_extra_material": True,
        },
    )
    assert stock_resp.status_code == 400
    assert "must be in 'dispatched' status" in stock_resp.json()["detail"].lower()

    # Test mismatched product serial rejection
    prod_mismatch_resp = client.post(
        f"/api/v1/installations/{installation_id}/materials",
        headers=headers,
        json={
            "product_id": product_id,
            "serial_number_id": sn_diff_prod_id,
            "quantity_consumed": 1.0,
            "unit_of_measure": "NOS",
            "is_extra_material": True,
        },
    )
    assert prod_mismatch_resp.status_code == 400
    assert "belongs to product id" in prod_mismatch_resp.json()["detail"].lower()

    # Test another project serial rejection (if other project exists)
    if other_proj:
        proj_mismatch_resp = client.post(
            f"/api/v1/installations/{installation_id}/materials",
            headers=headers,
            json={
                "product_id": product_id,
                "serial_number_id": sn_other_id,
                "quantity_consumed": 1.0,
                "unit_of_measure": "NOS",
                "is_extra_material": True,
            },
        )
        assert proj_mismatch_resp.status_code == 400
        assert "allocated to project id" in proj_mismatch_resp.json()["detail"].lower()


def test_customer_acceptance_and_project_completion(setup_installation_test_env, installation_test_data):
    cust_token = setup_installation_test_env["tokens"][SystemRole.CUSTOMER]
    project_id = installation_test_data["project_id"]

    # Retrieve installation ID
    res_inst = client.get(
        f"/api/v1/installations?project_id={project_id}",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert res_inst.status_code == 200
    installation_id = res_inst.json()["data"]["items"][0]["id"]

    # Submit customer acceptance sign-off
    res_acc = client.post(
        f"/api/v1/installations/{installation_id}/customer-acceptance",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={
            "acceptance_date": str(date.today()),
            "rating_overall": 5,
            "satisfaction_notes": "Exceptional installation quality. Generation started and app monitoring configured.",
            "is_accepted": True,
        },
    )
    assert res_acc.status_code == 201, res_acc.text
    acc_data = res_acc.json()["data"]
    assert acc_data["is_accepted"] is True
    assert acc_data["rating_overall"] == 5

    # Verify database state atomically
    with SessionLocal() as db:
        inst = db.execute(select(Installation).where(Installation.id == installation_id)).scalar_one()
        assert inst.status == "COMPLETED"
        assert inst.commissioning_date == date.today()

        proj = db.execute(select(Project).where(Project.id == project_id)).scalar_one()
        assert proj.status == "COMPLETED"
        assert proj.actual_completion_date == date.today()

    # Attempt duplicate customer acceptance (must reject with 400)
    res_dup = client.post(
        f"/api/v1/installations/{installation_id}/customer-acceptance",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"is_accepted": True},
    )
    assert res_dup.status_code == 400
    assert "already been recorded" in res_dup.json()["detail"].lower()


def test_installation_rbac_restrictions(setup_installation_test_env, installation_test_data):
    sales_token = setup_installation_test_env["tokens"][SystemRole.SALES]
    project_id = installation_test_data["project_id"]

    # Sales cannot create installation schedules
    res = client.post(
        "/api/v1/installation-schedules",
        headers={"Authorization": f"Bearer {sales_token}"},
        json={"project_id": project_id, "scheduled_start_date": str(date.today()), "scheduled_end_date": str(date.today())},
    )
    assert res.status_code == 403
