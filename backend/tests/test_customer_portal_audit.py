import pytest
from datetime import date, timedelta
from decimal import Decimal
import uuid
from starlette.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.database import SessionLocal
from app.models.auth import User, Role
from app.models.crm import Customer, Enquiry, Quotation
from app.models.projects import Project, Order
from app.models.installations import Installation, InstallationChecklist, InstallationTest, TechnicianWorklog
from app.utils.roles import SystemRole
from app.utils.security import hash_password, create_access_token

client = TestClient(app)

@pytest.fixture(scope="module")
def customer_auth():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "master_e2e_customer@sunpower.com", "password": "Pass123!Safe"},
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token_data = login_res.json()["data"]
    cust_token = token_data["access_token"]
    assert token_data["user"]["role"]["slug"] == SystemRole.CUSTOMER
    headers = {"Authorization": f"Bearer {cust_token}"}
    
    # Ensure profile exists
    me_res = client.get("/api/v1/customers/me", headers=headers)
    assert me_res.status_code == 200, f"Profile fetch failed: {me_res.text}"
    customer_id = me_res.json()["data"]["id"]
    return {"headers": headers, "customer_id": customer_id, "user_id": token_data["user"]["id"]}

def test_customer_portal_comprehensive_audit(customer_auth):
    headers = customer_auth["headers"]
    customer_id = customer_auth["customer_id"]

    # 1. Customer Login and Account Access
    # Verify customer cannot access employee endpoints
    emp_res = client.get("/api/v1/employees", headers=headers)
    assert emp_res.status_code == 403, "Customer must not access internal employees directory"

    # Verify customer cannot access procurement purchase orders or inventory
    proc_res = client.get("/api/v1/purchase-orders", headers=headers)
    assert proc_res.status_code == 403, "Customer must not access internal procurement"

    # 2. Customer Profile (View and Edit)
    me_res = client.get("/api/v1/customers/me", headers=headers)
    assert me_res.status_code == 200, f"Customers/me failed: {me_res.text}"
    prof = me_res.json()["data"]
    assert prof["email"] == "master_e2e_customer@sunpower.com"

    # Edit profile (Address, city, alternate_phone, meter number)
    update_res = client.put(
        "/api/v1/customers/me",
        headers=headers,
        json={
            "address": "42 Green Energy Enclave, Phase 2",
            "city": "Hyderabad",
            "state": "Telangana",
            "pincode": "500081",
            "alternate_phone": "9123456780",
            "electricity_consumer_number": f"DISCOM-{customer_id}-99",
        },
    )
    assert update_res.status_code == 200, f"Profile update failed: {update_res.text}"
    updated_prof = update_res.json()["data"]
    assert updated_prof["address"] == "42 Green Energy Enclave, Phase 2"
    assert updated_prof["electricity_consumer_number"] == f"DISCOM-{customer_id}-99"

    # 3. Enquiries and Solar Requirements
    # Submit solar requirement
    enq_create_res = client.post(
        "/api/v1/enquiries",
        headers=headers,
        json={
            "system_type": "ON_GRID",
            "proposed_capacity_kw": 4.5,
            "monthly_electricity_bill": 4200.0,
            "roof_type": "RCC_FLAT",
            "notes": "Interested in bifacial tier-1 monocrystalline panels with remote app monitoring",
            "customer_id": customer_id,
        },
    )
    assert enq_create_res.status_code == 201, f"Enquiry creation failed: {enq_create_res.text}"
    created_enq = enq_create_res.json()["data"]
    assert created_enq["customer_id"] == customer_id
    assert created_enq["status"] == "NEW"

    # List enquiries (scoped to customer)
    enq_list_res = client.get("/api/v1/enquiries", headers=headers)
    assert enq_list_res.status_code == 200, f"Enquiry list failed: {enq_list_res.text}"
    enq_items = enq_list_res.json()["data"]["items"]
    assert len(enq_items) >= 1
    assert any(e["id"] == created_enq["id"] for e in enq_items)

    # 4. Site Surveys (View scoped, schedule blocked)
    surv_list_res = client.get("/api/v1/surveys", headers=headers)
    assert surv_list_res.status_code == 200, f"Survey list failed: {surv_list_res.text}"
    # Verify customer cannot schedule internal survey
    surv_sched_res = client.post(
        "/api/v1/surveys",
        headers=headers,
        json={"enquiry_id": created_enq["id"], "surveyor_id": 1, "scheduled_at": str(date.today())},
    )
    assert surv_sched_res.status_code == 403, "Customer must not schedule internal site surveys"

    # 5. Quotations (View scoped, accept & reject)
    quotes_res = client.get("/api/v1/quotations", headers=headers)
    assert quotes_res.status_code == 200, f"Quotations list failed: {quotes_res.text}"

    # 6. Orders and Projects (Scoped)
    orders_res = client.get("/api/v1/orders", headers=headers)
    assert orders_res.status_code == 200, f"Orders list failed: {orders_res.text}"

    projects_res = client.get("/api/v1/projects", headers=headers)
    assert projects_res.status_code == 200, f"Projects list failed: {projects_res.text}"

    # 7. Invoices & Payments (Scoped)
    inv_res = client.get("/api/v1/invoices", headers=headers)
    assert inv_res.status_code == 200, f"Invoices list failed: {inv_res.text}"

    pay_res = client.get("/api/v1/payments", headers=headers)
    assert pay_res.status_code == 200, f"Payments list failed: {pay_res.text}"

    # 8. Warranties & Service Tickets (Scoped)
    war_res = client.get("/api/v1/warranty", headers=headers)
    assert war_res.status_code == 200, f"Warranty list failed: {war_res.text}"

    tick_res = client.get("/api/v1/service-tickets", headers=headers)
    assert tick_res.status_code == 200, f"Tickets list failed: {tick_res.text}"

    # 9. Subsidy Tracking (Scoped)
    sub_res = client.get("/api/v1/subsidy/applications", headers=headers)
    assert sub_res.status_code == 200, f"Subsidy list failed: {sub_res.text}"

    # 10. Data Security Guard: Cannot access another customer's data
    other_cust_res = client.get("/api/v1/customers/404", headers=headers)
    assert other_cust_res.status_code == 403, "Customer must not view other customer records"


def test_customer_profile_security_and_immutability(customer_auth):
    headers = customer_auth["headers"]
    
    # Attempt to change immutable/sensitive fields (e.g., trying to escalate role or change user_id)
    # The endpoint only extracts address, city, state, pincode, full_name, alternate_phone, electricity_consumer_number
    # It rejects invalid consumer number duplicates if someone uses an existing one
    res = client.put(
        "/api/v1/customers/me",
        headers=headers,
        json={
            "user_id": 1,  # Attempt tampering
            "customer_type": "COMMERCIAL",  # Attempt tampering
            "is_active": False,  # Attempt tampering
            "city": "Secunderabad",
        },
    )
    assert res.status_code == 200
    data = res.json()["data"]
    # Verify customer_type did not change
    assert data["customer_type"] == "RESIDENTIAL"
    assert data["user_id"] == customer_auth["user_id"]
    assert data["city"] == "Secunderabad"


def test_customer_enquiry_capacity_validation(customer_auth):
    headers = customer_auth["headers"]
    customer_id = customer_auth["customer_id"]

    # Residential capacity cannot exceed 5.0 kW per business rule
    res = client.post(
        "/api/v1/enquiries",
        headers=headers,
        json={
            "system_type": "ON_GRID",
            "proposed_capacity_kw": 25.0,
            "monthly_electricity_bill": 20000.0,
            "roof_type": "RCC_FLAT",
            "notes": "Too large for residential",
            "customer_id": customer_id,
        },
    )
    assert res.status_code == 400
    assert "Residential rooftop solar capacity must be between 1.0 kW and 5.0 kW" in res.json()["detail"]


def test_customer_cross_boundary_isolation(customer_auth):
    headers = customer_auth["headers"]

    # Customer cannot access internal warehouse dispatch endpoint
    disp_res = client.get("/api/v1/dispatches", headers=headers)
    assert disp_res.status_code == 403, "Customer must not access internal dispatches"

    # Customer cannot access CRM admin dashboard/analytics
    crm_res = client.get("/api/v1/crm/dashboard", headers=headers)
    assert crm_res.status_code == 403, "Customer must not access internal CRM analytics"

    # Customer cannot access financial supplier invoices
    supp_res = client.get("/api/v1/supplier-invoices", headers=headers)
    assert supp_res.status_code == 403, "Customer must not access supplier finance"

    # Customer cannot access internal project profitability
    prof_res = client.get("/api/v1/projects/1/profitability", headers=headers)
    assert prof_res.status_code == 403, "Customer must not access project profitability"


def _create_project_and_installation(db, cust, created_by_user_id, uid, capacity=Decimal("4.0"), proj_status="INSTALLATION"):
    enq = Enquiry(
        enquiry_number=f"ENQ-{uid}",
        customer_id=cust.id,
        source="DIRECT",
        system_type="ON_GRID",
        proposed_capacity_kw=capacity,
        monthly_electricity_bill=Decimal("4000.00"),
        status="WON",
    )
    db.add(enq)
    db.flush()

    quo = Quotation(
        quotation_number=f"Q-{uid}",
        enquiry_id=enq.id,
        version=1,
        system_type="ON_GRID",
        capacity_kw=capacity,
        total_product_cost=Decimal("200000.00"),
        installation_cost=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        gross_amount=Decimal("200000.00"),
        subsidy_estimate=Decimal("0.00"),
        net_payable_amount=Decimal("200000.00"),
        valid_until=date.today() + timedelta(days=30),
        quotation_date=date.today(),
        status="ACCEPTED",
        created_by=created_by_user_id,
    )
    db.add(quo)
    db.flush()

    order = Order(
        order_number=f"ORD-{uid}",
        customer_id=cust.id,
        quotation_id=quo.id,
        order_date=date.today(),
        total_amount=Decimal("200000.00"),
        advance_paid=Decimal("50000.00"),
        balance_amount=Decimal("150000.00"),
        status="CONFIRMED",
        created_by=created_by_user_id,
    )
    db.add(order)
    db.flush()

    proj = Project(
        project_code=f"PRJ-{uid}",
        order_id=order.id,
        customer_id=cust.id,
        system_capacity_kw=capacity,
        system_type="ON_GRID",
        site_address=cust.address,
        planned_start_date=date.today(),
        planned_completion_date=date.today() + timedelta(days=30),
        status=proj_status,
    )
    db.add(proj)
    db.flush()

    inst = Installation(
        project_id=proj.id,
        status="IN_PROGRESS",
        lead_technician_id=1,
        system_capacity_kw=capacity,
        inverter_make_model=f"SunPower {capacity}kW",
        total_panels_installed=8,
        installation_date=date.today(),
        technician_notes=f"Confidential technician observations for project {uid}",
    )
    db.add(inst)
    db.flush()

    return proj, inst


@pytest.fixture(scope="module")
def two_customers_env():
    uid_a = uuid.uuid4().hex[:6]
    uid_b = uuid.uuid4().hex[:6]

    with SessionLocal() as db:
        cust_role = db.execute(select(Role).where(Role.slug == SystemRole.CUSTOMER)).scalar_one()
        admin_role = db.execute(select(Role).where(Role.slug == SystemRole.SUPER_ADMIN)).scalar_one()

        # Admin user
        admin_user = User(
            role_id=admin_role.id,
            email=f"admin_iso_{uid_a}@sunpower.com",
            full_name=f"Admin {uid_a}",
            hashed_password=hash_password("Pass123!Safe"),
            is_active=True,
            is_verified=True,
        )
        db.add(admin_user)
        db.flush()
        admin_token = create_access_token({"sub": str(admin_user.id), "role": SystemRole.SUPER_ADMIN})

        # Customer A
        user_a = User(
            role_id=cust_role.id,
            email=f"cust_a_{uid_a}@example.com",
            full_name=f"Customer A {uid_a}",
            hashed_password=hash_password("Pass123!Safe"),
            is_active=True,
            is_verified=True,
        )
        db.add(user_a)
        db.flush()
        token_a = create_access_token({"sub": str(user_a.id), "role": SystemRole.CUSTOMER})

        cust_a = Customer(
            user_id=user_a.id,
            customer_type="RESIDENTIAL",
            full_name=f"Customer A {uid_a}",
            phone=f"91111{uid_a[:5]}",
            email=user_a.email,
            address="100 A Street",
            city="Bengaluru",
            state="Karnataka",
            pincode="560001",
            created_by=admin_user.id,
            is_active=True,
        )
        db.add(cust_a)
        db.flush()

        proj_a, inst_a = _create_project_and_installation(db, cust_a, admin_user.id, uid_a, Decimal("4.0"), "INSTALLATION")

        cl_a = InstallationChecklist(
            installation_id=inst_a.id,
            checklist_item="Structure Fastening",
            category="MECHANICAL",
            is_checked=False,
        )
        db.add(cl_a)

        wl_a = TechnicianWorklog(
            installation_id=inst_a.id,
            employee_id=1,
            work_date=date.today(),
            hours_worked=Decimal("6.0"),
            work_description="Confidential technician worklog on mounting brackets",
        )
        db.add(wl_a)

        # Customer B
        user_b = User(
            role_id=cust_role.id,
            email=f"cust_b_{uid_b}@example.com",
            full_name=f"Customer B {uid_b}",
            hashed_password=hash_password("Pass123!Safe"),
            is_active=True,
            is_verified=True,
        )
        db.add(user_b)
        db.flush()
        token_b = create_access_token({"sub": str(user_b.id), "role": SystemRole.CUSTOMER})

        cust_b = Customer(
            user_id=user_b.id,
            customer_type="RESIDENTIAL",
            full_name=f"Customer B {uid_b}",
            phone=f"92222{uid_b[:5]}",
            email=user_b.email,
            address="200 B Street",
            city="Mysuru",
            state="Karnataka",
            pincode="570001",
            created_by=admin_user.id,
            is_active=True,
        )
        db.add(cust_b)
        db.flush()

        proj_b, inst_b = _create_project_and_installation(db, cust_b, admin_user.id, uid_b, Decimal("5.0"), "INSTALLATION")

        cl_b = InstallationChecklist(
            installation_id=inst_b.id,
            checklist_item="Inverter Earth Resistance",
            category="ELECTRICAL",
            is_checked=False,
        )
        db.add(cl_b)

        db.commit()

        return {
            "token_a": token_a,
            "cust_a_id": cust_a.id,
            "proj_a_id": proj_a.id,
            "inst_a_id": inst_a.id,
            "cl_a_id": cl_a.id,
            "token_b": token_b,
            "cust_b_id": cust_b.id,
            "proj_b_id": proj_b.id,
            "inst_b_id": inst_b.id,
            "admin_token": admin_token,
        }


def test_installation_data_isolation(two_customers_env):
    env = two_customers_env
    headers_a = {"Authorization": f"Bearer {env['token_a']}"}
    headers_b = {"Authorization": f"Bearer {env['token_b']}"}
    headers_admin = {"Authorization": f"Bearer {env['admin_token']}"}

    # 1. Customer A list installations: returns only Project A's installation
    res_a = client.get("/api/v1/installations", headers=headers_a)
    assert res_a.status_code == 200
    items_a = res_a.json()["data"]["items"]
    assert len(items_a) >= 1
    assert all(it["project_id"] == env["proj_a_id"] for it in items_a)
    assert not any(it["project_id"] == env["proj_b_id"] for it in items_a)
    # Masked notes in list
    inst_a_in_list = [it for it in items_a if it["id"] == env["inst_a_id"]][0]
    assert inst_a_in_list["technician_notes"] is None

    # 2. Customer B list installations: returns only Project B's installation
    res_b = client.get("/api/v1/installations", headers=headers_b)
    assert res_b.status_code == 200
    items_b = res_b.json()["data"]["items"]
    assert len(items_b) >= 1
    assert all(it["project_id"] == env["proj_b_id"] for it in items_b)
    assert not any(it["project_id"] == env["proj_a_id"] for it in items_b)

    # 3. Cross-customer direct ID access: Customer A cannot view Customer B's installation
    res_cross = client.get(f"/api/v1/installations/{env['inst_b_id']}", headers=headers_a)
    assert res_cross.status_code == 403
    assert "own projects" in res_cross.json()["detail"].lower()

    # 4. Project ID bypass attempt: Customer A queries using Customer B's project_id
    res_bypass = client.get(f"/api/v1/installations?project_id={env['proj_b_id']}", headers=headers_a)
    assert res_bypass.status_code == 403
    assert "own customer account" in res_bypass.json()["detail"].lower()

    # 5. Cross-customer checklists access denial
    res_cross_cl = client.get(f"/api/v1/installations/{env['inst_b_id']}/checklists", headers=headers_a)
    assert res_cross_cl.status_code == 403

    # 6. Detail masking: Customer A gets own detail, but notes and worklogs are masked
    res_detail_a = client.get(f"/api/v1/installations/{env['inst_a_id']}", headers=headers_a)
    assert res_detail_a.status_code == 200
    data_a = res_detail_a.json()["data"]
    assert data_a["technician_notes"] is None
    assert len(data_a.get("worklogs", [])) == 0

    # 7. Authorized employee retains full view with unmasked notes and worklogs
    res_admin = client.get(f"/api/v1/installations/{env['inst_a_id']}", headers=headers_admin)
    assert res_admin.status_code == 200
    data_admin = res_admin.json()["data"]
    assert "Confidential technician observations for project" in data_admin["technician_notes"]
    assert len(data_admin.get("worklogs", [])) > 0


def test_customer_acceptance_safety_lifecycle(two_customers_env):
    env = two_customers_env
    headers_a = {"Authorization": f"Bearer {env['token_a']}"}
    headers_b = {"Authorization": f"Bearer {env['token_b']}"}
    inst_a_id = env["inst_a_id"]
    proj_a_id = env["proj_a_id"]

    # 1. Non-existent installation returns 404
    res_404 = client.post("/api/v1/installations/999999/customer-acceptance", headers=headers_a, json={"is_accepted": True})
    assert res_404.status_code == 404

    # 2. Cross-customer acceptance attempt: Customer B attempts to accept Customer A's installation -> 403
    res_cross_acc = client.post(f"/api/v1/installations/{inst_a_id}/customer-acceptance", headers=headers_b, json={"is_accepted": True})
    assert res_cross_acc.status_code == 403

    # 3. Acceptance blocked because checklist item is not verified -> 400
    res_cl_fail = client.post(f"/api/v1/installations/{inst_a_id}/customer-acceptance", headers=headers_a, json={"is_accepted": True})
    assert res_cl_fail.status_code == 400
    assert "checklist item" in res_cl_fail.json()["detail"].lower()

    # Verify the checklist item in db
    with SessionLocal() as db:
        cl = db.get(InstallationChecklist, env["cl_a_id"])
        cl.is_checked = True
        cl.verified_by = 1
        db.commit()

    # 4. Acceptance blocked because electrical tests are missing -> 400
    res_test_missing = client.post(f"/api/v1/installations/{inst_a_id}/customer-acceptance", headers=headers_a, json={"is_accepted": True})
    assert res_test_missing.status_code == 400
    assert "electrical commissioning tests" in res_test_missing.json()["detail"].lower()

    # Add a failed electrical test
    with SessionLocal() as db:
        t_fail = InstallationTest(
            installation_id=inst_a_id,
            test_name="EARTHING_CONTINUITY",
            measured_value="15.5",
            unit_of_measure="Ohms",
            test_date=date.today(),
            tested_by=1,
            is_passed=False,
            remarks="High resistance",
        )
        db.add(t_fail)
        db.commit()
        t_fail_id = t_fail.id

    # 5. Acceptance blocked because electrical test failed -> 400
    res_test_fail = client.post(f"/api/v1/installations/{inst_a_id}/customer-acceptance", headers=headers_a, json={"is_accepted": True})
    assert res_test_fail.status_code == 400
    assert "safety tests failed" in res_test_fail.json()["detail"].lower()

    # Fix the test to passed
    with SessionLocal() as db:
        t = db.get(InstallationTest, t_fail_id)
        t.is_passed = True
        t.remarks = "Passed after earthing electrode rebonding"
        db.commit()

    # 6. All prerequisites satisfied: acceptance succeeds -> 201
    res_ok = client.post(
        f"/api/v1/installations/{inst_a_id}/customer-acceptance",
        headers=headers_a,
        json={
            "acceptance_date": str(date.today()),
            "rating_overall": 5,
            "satisfaction_notes": "All checks and safety tests completed to perfection.",
            "is_accepted": True,
        },
    )
    assert res_ok.status_code == 201, res_ok.text
    acc_data = res_ok.json()["data"]
    assert acc_data["is_accepted"] is True
    assert acc_data["rating_overall"] == 5

    # Verify atomic state change in DB
    with SessionLocal() as db:
        inst_db = db.get(Installation, inst_a_id)
        assert inst_db.status == "COMPLETED"
        assert inst_db.commissioning_date == date.today()
        proj_db = db.get(Project, proj_a_id)
        assert proj_db.status == "COMPLETED"
        assert proj_db.actual_completion_date == date.today()

    # 7. Duplicate acceptance attempt returns 400
    res_dup = client.post(
        f"/api/v1/installations/{inst_a_id}/customer-acceptance",
        headers=headers_a,
        json={"is_accepted": True},
    )
    assert res_dup.status_code == 400
    assert "already been recorded" in res_dup.json()["detail"].lower()


def test_customer_acceptance_invalid_project_status(two_customers_env):
    env = two_customers_env
    uid = uuid.uuid4().hex[:6]

    with SessionLocal() as db:
        cust_role = db.execute(select(Role).where(Role.slug == SystemRole.CUSTOMER)).scalar_one()
        user_c = User(
            role_id=cust_role.id,
            email=f"cust_c_{uid}@example.com",
            full_name=f"Customer C {uid}",
            hashed_password=hash_password("Pass123!Safe"),
            is_active=True,
            is_verified=True,
        )
        db.add(user_c)
        db.flush()
        token_c = create_access_token({"sub": str(user_c.id), "role": SystemRole.CUSTOMER})

        cust_c = Customer(
            user_id=user_c.id,
            customer_type="RESIDENTIAL",
            full_name=f"Customer C {uid}",
            phone=f"93333{uid[:5]}",
            email=user_c.email,
            address="300 C Street",
            city="Bengaluru",
            state="Karnataka",
            pincode="560001",
            created_by=1,
            is_active=True,
        )
        db.add(cust_c)
        db.flush()

        # Project in PLANNING status (invalid for acceptance)
        proj_c, inst_c = _create_project_and_installation(db, cust_c, 1, uid, Decimal("3.0"), "PLANNING")
        db.commit()

        inst_c_id = inst_c.id

    # Acceptance on PLANNING project must reject with 400
    res = client.post(
        f"/api/v1/installations/{inst_c_id}/customer-acceptance",
        headers={"Authorization": f"Bearer {token_c}"},
        json={"is_accepted": True},
    )
    assert res.status_code == 400
    assert "invalid operational status" in res.json()["detail"].lower()
