import pytest
import uuid
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.main import app
from app.database import SessionLocal
from app.models.auth import User, Role, Department, Employee
from app.models.crm import Customer, Enquiry, Followup
from app.utils.roles import SystemRole
from app.utils.security import hash_password, create_access_token
from app.services.seed import seed_reference_data

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_crm_auth_tokens():
    db = SessionLocal()
    try:
        seed_reference_data(db)

        sa_role = db.execute(select(Role).where(Role.slug == SystemRole.SUPER_ADMIN)).scalar_one()
        dir_role = db.execute(select(Role).where(Role.slug == SystemRole.DIRECTOR)).scalar_one()
        sales_role = db.execute(select(Role).where(Role.slug == SystemRole.SALES)).scalar_one()
        cust_role = db.execute(select(Role).where(Role.slug == SystemRole.CUSTOMER)).scalar_one()

        dept = db.execute(select(Department).where(Department.code == "SALES_SEC")).scalar_one_or_none()
        if not dept:
            dept = Department(name="Sales Security Dept", code="SALES_SEC", is_active=True)
            db.add(dept)
            db.commit()
            db.refresh(dept)

        # 1. Super Admin User
        admin_user = db.execute(select(User).where(User.email == "sec_admin@sunpower.com")).scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                role_id=sa_role.id,
                email="sec_admin@sunpower.com",
                full_name="Sec Super Admin",
                hashed_password=hash_password("AdminPass123!"),
                is_active=True,
                is_verified=True,
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

        # 2. Director User
        director_user = db.execute(select(User).where(User.email == "sec_director@sunpower.com")).scalar_one_or_none()
        if not director_user:
            director_user = User(
                role_id=dir_role.id,
                email="sec_director@sunpower.com",
                full_name="Sec Director",
                hashed_password=hash_password("DirectorPass123!"),
                is_active=True,
                is_verified=True,
            )
            db.add(director_user)
            db.commit()
            db.refresh(director_user)

        # 3. Sales Rep A
        sales_a_user = db.execute(select(User).where(User.email == "sec_sales_a@sunpower.com")).scalar_one_or_none()
        if not sales_a_user:
            sales_a_user = User(
                role_id=sales_role.id,
                email="sec_sales_a@sunpower.com",
                full_name="Sales Rep Alice",
                phone="9876500001",
                hashed_password=hash_password("SalesPass123!"),
                is_active=True,
                is_verified=True,
            )
            db.add(sales_a_user)
            db.commit()
            db.refresh(sales_a_user)

        sales_a_emp = db.execute(select(Employee).where(Employee.user_id == sales_a_user.id)).scalar_one_or_none()
        if not sales_a_emp:
            sales_a_emp = Employee(
                user_id=sales_a_user.id,
                department_id=dept.id,
                employee_code="EMP-REP-A",
                designation="Sales Representative A",
                employment_type="FULL_TIME",
                joining_date=datetime.now(timezone.utc).date(),
                is_active=True,
            )
            db.add(sales_a_emp)
            db.commit()
            db.refresh(sales_a_emp)

        # 4. Sales Rep B
        sales_b_user = db.execute(select(User).where(User.email == "sec_sales_b@sunpower.com")).scalar_one_or_none()
        if not sales_b_user:
            sales_b_user = User(
                role_id=sales_role.id,
                email="sec_sales_b@sunpower.com",
                full_name="Sales Rep Bob",
                phone="9876500002",
                hashed_password=hash_password("SalesPass123!"),
                is_active=True,
                is_verified=True,
            )
            db.add(sales_b_user)
            db.commit()
            db.refresh(sales_b_user)

        sales_b_emp = db.execute(select(Employee).where(Employee.user_id == sales_b_user.id)).scalar_one_or_none()
        if not sales_b_emp:
            sales_b_emp = Employee(
                user_id=sales_b_user.id,
                department_id=dept.id,
                employee_code="EMP-REP-B",
                designation="Sales Representative B",
                employment_type="FULL_TIME",
                joining_date=datetime.now(timezone.utc).date(),
                is_active=True,
            )
            db.add(sales_b_emp)
            db.commit()
            db.refresh(sales_b_emp)

        # 5. Customer User
        cust_user = db.execute(select(User).where(User.email == "sec_cust@sunpower.com")).scalar_one_or_none()
        if not cust_user:
            cust_user = User(
                role_id=cust_role.id,
                email="sec_cust@sunpower.com",
                full_name="Sec Customer",
                hashed_password=hash_password("CustPass123!"),
                is_active=True,
                is_verified=True,
            )
            db.add(cust_user)
            db.commit()
            db.refresh(cust_user)

        admin_token = create_access_token({"sub": str(admin_user.id), "email": admin_user.email, "role": sa_role.slug})
        dir_token = create_access_token({"sub": str(director_user.id), "email": director_user.email, "role": dir_role.slug})
        sales_a_token = create_access_token({"sub": str(sales_a_user.id), "email": sales_a_user.email, "role": sales_role.slug})
        sales_b_token = create_access_token({"sub": str(sales_b_user.id), "email": sales_b_user.email, "role": sales_role.slug})
        cust_token = create_access_token({"sub": str(cust_user.id), "email": cust_user.email, "role": cust_role.slug})

        return {
            "admin": {"headers": {"Authorization": f"Bearer {admin_token}"}, "user_id": admin_user.id},
            "director": {"headers": {"Authorization": f"Bearer {dir_token}"}, "user_id": director_user.id},
            "sales_a": {"headers": {"Authorization": f"Bearer {sales_a_token}"}, "user_id": sales_a_user.id, "employee_id": sales_a_emp.id},
            "sales_b": {"headers": {"Authorization": f"Bearer {sales_b_token}"}, "user_id": sales_b_user.id, "employee_id": sales_b_emp.id},
            "customer": {"headers": {"Authorization": f"Bearer {cust_token}"}, "user_id": cust_user.id},
        }
    finally:
        db.close()


def test_sales_representative_data_isolation(setup_crm_auth_tokens):
    headers_a = setup_crm_auth_tokens["sales_a"]["headers"]
    emp_a_id = setup_crm_auth_tokens["sales_a"]["employee_id"]

    headers_b = setup_crm_auth_tokens["sales_b"]["headers"]
    emp_b_id = setup_crm_auth_tokens["sales_b"]["employee_id"]

    dir_headers = setup_crm_auth_tokens["director"]["headers"]
    admin_headers = setup_crm_auth_tokens["admin"]["headers"]
    cust_headers = setup_crm_auth_tokens["customer"]["headers"]

    # 1. Register customer & create enquiry assigned to Rep A
    suffix = uuid.uuid4().hex[:6]
    res_cust = client.post(
        "/api/v1/customers",
        json={
            "customer_type": "RESIDENTIAL",
            "full_name": f"Client Iso {suffix}",
            "phone": f"9{suffix}123"[:10],
            "address": "123 Isolation Lane",
            "city": "Hyderabad",
            "state": "Telangana",
            "pincode": "500081",
        },
        headers=headers_a,
    )
    assert res_cust.status_code == 201
    cust_id = res_cust.json()["data"]["id"]

    res_enq_a = client.post(
        "/api/v1/enquiries",
        json={
            "customer_id": cust_id,
            "proposed_capacity_kw": 3.0,
            "assigned_sales_id": emp_a_id,
            "system_type": "ON_GRID",
        },
        headers=headers_a,
    )
    assert res_enq_a.status_code == 201
    enq_a_id = res_enq_a.json()["data"]["id"]

    # 2. Rep B cannot see Rep A's enquiry in the list
    res_list_b = client.get("/api/v1/enquiries", headers=headers_b)
    assert res_list_b.status_code == 200
    b_enq_ids = [item["id"] for item in res_list_b.json()["data"]["items"]]
    assert enq_a_id not in b_enq_ids

    # 3. Rep B is rejected (403) from getting detail of Rep A's enquiry
    res_get_b = client.get(f"/api/v1/enquiries/{enq_a_id}", headers=headers_b)
    assert res_get_b.status_code == 403

    # 4. Rep B is rejected (403) from updating Rep A's enquiry
    res_up_b = client.put(f"/api/v1/enquiries/{enq_a_id}", json={"notes": "Hacked by B"}, headers=headers_b)
    assert res_up_b.status_code == 403

    # 5. Rep B is rejected (403) from updating status of Rep A's enquiry
    res_stat_b = client.put(f"/api/v1/enquiries/{enq_a_id}/status", json={"status": "CONTACTED"}, headers=headers_b)
    assert res_stat_b.status_code == 403

    # 6. Rep B is rejected (403) from reassigning Rep A's enquiry
    res_asgn_b = client.put(f"/api/v1/enquiries/{enq_a_id}/assign", json={"assigned_sales_id": emp_b_id}, headers=headers_b)
    assert res_asgn_b.status_code == 403

    # 7. Follow-up isolation: Rep A schedules follow-up; Rep B cannot access or complete it
    res_f_a = client.post(
        "/api/v1/followups",
        json={
            "enquiry_id": enq_a_id,
            "followup_type": "CALL",
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        },
        headers=headers_a,
    )
    assert res_f_a.status_code == 201
    f_a_id = res_f_a.json()["data"]["id"]

    # Rep B cannot see follow-up A in listing
    res_f_list_b = client.get("/api/v1/followups", headers=headers_b)
    assert res_f_list_b.status_code == 200
    b_f_ids = [item["id"] for item in res_f_list_b.json()["data"]["items"]]
    assert f_a_id not in b_f_ids

    # Rep B cannot complete Rep A's follow-up
    res_f_comp_b = client.put(
        f"/api/v1/followups/{f_a_id}/complete",
        json={"discussion_summary": "Completed by unauthorized rep B"},
        headers=headers_b,
    )
    assert res_f_comp_b.status_code == 403

    # Rep B cannot reschedule Rep A's follow-up
    res_f_resched_b = client.put(
        f"/api/v1/followups/{f_a_id}/reschedule",
        json={"scheduled_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(), "reason": "Postpone by B"},
        headers=headers_b,
    )
    assert res_f_resched_b.status_code == 403

    # 8. Director and Super Admin have broader oversight
    res_dir_get = client.get(f"/api/v1/enquiries/{enq_a_id}", headers=dir_headers)
    assert res_dir_get.status_code == 200
    assert res_dir_get.json()["data"]["id"] == enq_a_id

    # Director can reassign enquiry A to Rep B
    res_dir_reassign = client.put(f"/api/v1/enquiries/{enq_a_id}/assign", json={"assigned_sales_id": emp_b_id}, headers=dir_headers)
    assert res_dir_reassign.status_code == 200
    assert res_dir_reassign.json()["data"]["assigned_sales_id"] == emp_b_id

    # Customer role is strictly rejected
    res_cust_get = client.get(f"/api/v1/enquiries/{enq_a_id}", headers=cust_headers)
    assert res_cust_get.status_code == 403


def test_enquiry_number_concurrency_and_retry(setup_crm_auth_tokens, monkeypatch):
    headers = setup_crm_auth_tokens["sales_a"]["headers"]
    emp_id = setup_crm_auth_tokens["sales_a"]["employee_id"]

    # Register customer
    suffix = uuid.uuid4().hex[:6]
    res_c = client.post(
        "/api/v1/customers",
        json={
            "customer_type": "RESIDENTIAL",
            "full_name": f"Retry Cust {suffix}",
            "phone": f"8{suffix}456"[:10],
            "address": "456 Solar Loop",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560001",
        },
        headers=headers,
    )
    cust_id = res_c.json()["data"]["id"]

    # 1. Normal enquiry creation maintains ENQ-YYYYMMDD-XXXX
    res_normal = client.post(
        "/api/v1/enquiries",
        json={"customer_id": cust_id, "proposed_capacity_kw": 4.0},
        headers=headers,
    )
    assert res_normal.status_code == 201
    enq_num = res_normal.json()["data"]["enquiry_number"]
    assert enq_num.startswith("ENQ-")
    parts = enq_num.split("-")
    assert len(parts) == 3
    assert len(parts[1]) == 8  # YYYYMMDD
    assert len(parts[2]) == 4  # XXXX

    # 2. Simulate uniqueness collision with mock to verify rollback and retry behavior
    import app.routers.enquiries as enq_module
    original_gen = enq_module._generate_enquiry_number
    collision_tracker = {"calls": 0}

    def mock_gen(db):
        collision_tracker["calls"] += 1
        if collision_tracker["calls"] == 1:
            # First attempt collides with existing enquiry_number, raising real PostgreSQL IntegrityError
            return enq_num
        # Second attempt generates a fresh valid number
        return original_gen(db)

    monkeypatch.setattr(enq_module, "_generate_enquiry_number", mock_gen)

    # Test that catching IntegrityError and retrying succeeds
    res_retry = client.post(
        "/api/v1/enquiries",
        json={"customer_id": cust_id, "proposed_capacity_kw": 3.5},
        headers=headers,
    )
    assert res_retry.status_code == 201
    assert collision_tracker["calls"] == 2
    retry_enq_num = res_retry.json()["data"]["enquiry_number"]
    assert retry_enq_num != enq_num
    assert retry_enq_num.startswith("ENQ-")

    # 3. Simulate continuous collision exhausting max_retries (3 attempts) -> returns 409 Conflict
    monkeypatch.setattr(enq_module, "_generate_enquiry_number", lambda db: enq_num)
    res_exhausted = client.post(
        "/api/v1/enquiries",
        json={"customer_id": cust_id, "proposed_capacity_kw": 2.5},
        headers=headers,
    )
    assert res_exhausted.status_code == 409
    assert "Unable to generate a unique enquiry number" in res_exhausted.json()["detail"]


def test_followup_rescheduling_and_state_rules(setup_crm_auth_tokens):
    headers = setup_crm_auth_tokens["sales_a"]["headers"]
    emp_id = setup_crm_auth_tokens["sales_a"]["employee_id"]

    # Register customer & enquiry
    suffix = uuid.uuid4().hex[:6]
    res_c = client.post(
        "/api/v1/customers",
        json={
            "customer_type": "RESIDENTIAL",
            "full_name": f"Followup Lead {suffix}",
            "phone": f"7{suffix}789"[:10],
            "address": "789 Sunway Path",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "pincode": "600001",
        },
        headers=headers,
    )
    cust_id = res_c.json()["data"]["id"]

    res_e = client.post(
        "/api/v1/enquiries",
        json={"customer_id": cust_id, "proposed_capacity_kw": 2.5},
        headers=headers,
    )
    enq_id = res_e.json()["data"]["id"]

    # 1. Schedule a follow-up
    orig_time = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
    res_f = client.post(
        "/api/v1/followups",
        json={
            "enquiry_id": enq_id,
            "followup_type": "CALL",
            "scheduled_at": orig_time,
            "discussion_summary": "Initial scheduled call",
        },
        headers=headers,
    )
    assert res_f.status_code == 201
    f_id = res_f.json()["data"]["id"]

    # 2. Rescheduling SCHEDULED follow-up succeeds and preserves reason in discussion_summary
    new_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    res_resched = client.put(
        f"/api/v1/followups/{f_id}/reschedule",
        json={"scheduled_at": new_time, "reason": "Customer requested callback after office hours"},
        headers=headers,
    )
    assert res_resched.status_code == 200
    resched_data = res_resched.json()["data"]
    assert resched_data["status"] == "SCHEDULED"
    assert "Rescheduled to" in resched_data["discussion_summary"]
    assert "Customer requested callback after office hours" in resched_data["discussion_summary"]

    # 3. Complete the follow-up
    res_comp = client.put(
        f"/api/v1/followups/{f_id}/complete",
        json={"discussion_summary": "Call completed successfully. Sizing verified."},
        headers=headers,
    )
    assert res_comp.status_code == 200
    assert res_comp.json()["data"]["status"] == "COMPLETED"

    # 4. Attempting to reschedule COMPLETED follow-up fails with 400
    res_bad_resched = client.put(
        f"/api/v1/followups/{f_id}/reschedule",
        json={"scheduled_at": new_time, "reason": "Try to reschedule completed"},
        headers=headers,
    )
    assert res_bad_resched.status_code == 400
    assert "Only SCHEDULED follow-ups may be rescheduled" in res_bad_resched.json()["detail"]


def test_customer_type_specific_capacity_validation(setup_crm_auth_tokens):
    headers = setup_crm_auth_tokens["sales_a"]["headers"]

    suffix = uuid.uuid4().hex[:6]

    # 1. Residential customer
    res_res_cust = client.post(
        "/api/v1/customers",
        json={
            "customer_type": "RESIDENTIAL",
            "full_name": f"Res Customer {suffix}",
            "phone": f"6{suffix}101"[:10],
            "address": "Residential Colony",
            "city": "Hyderabad",
            "state": "Telangana",
            "pincode": "500001",
        },
        headers=headers,
    )
    assert res_res_cust.status_code == 201
    res_cust_id = res_res_cust.json()["data"]["id"]

    # Residential 1.0 kW succeeds (Minimum allowed)
    res_1kw = client.post("/api/v1/enquiries", json={"customer_id": res_cust_id, "proposed_capacity_kw": 1.0}, headers=headers)
    assert res_1kw.status_code == 201

    # Residential 5.0 kW succeeds (Maximum allowed)
    res_5kw = client.post("/api/v1/enquiries", json={"customer_id": res_cust_id, "proposed_capacity_kw": 5.0}, headers=headers)
    assert res_5kw.status_code == 201
    enq_5kw_id = res_5kw.json()["data"]["id"]

    # Residential below 1.0 kW fails (e.g. 0.8 kW)
    res_low = client.post("/api/v1/enquiries", json={"customer_id": res_cust_id, "proposed_capacity_kw": 0.8}, headers=headers)
    assert res_low.status_code == 400
    assert "must be between 1.0 kW and 5.0 kW" in res_low.json()["detail"]

    # Residential above 5.0 kW fails (e.g. 6.0 kW)
    res_high = client.post("/api/v1/enquiries", json={"customer_id": res_cust_id, "proposed_capacity_kw": 6.0}, headers=headers)
    assert res_high.status_code == 400
    assert "must be between 1.0 kW and 5.0 kW" in res_high.json()["detail"]

    # Updating residential enquiry with invalid capacity fails
    res_up_bad = client.put(f"/api/v1/enquiries/{enq_5kw_id}", json={"proposed_capacity_kw": 12.0}, headers=headers)
    assert res_up_bad.status_code == 400
    assert "must be between 1.0 kW and 5.0 kW" in res_up_bad.json()["detail"]

    # 2. Commercial customer
    res_comm_cust = client.post(
        "/api/v1/customers",
        json={
            "customer_type": "COMMERCIAL",
            "full_name": f"Commercial Customer {suffix}",
            "phone": f"6{suffix}202"[:10],
            "address": "IT Park Tower 1",
            "city": "Hyderabad",
            "state": "Telangana",
            "pincode": "500081",
        },
        headers=headers,
    )
    comm_cust_id = res_comm_cust.json()["data"]["id"]

    # Commercial 25.0 kW succeeds
    res_comm_25 = client.post("/api/v1/enquiries", json={"customer_id": comm_cust_id, "proposed_capacity_kw": 25.0}, headers=headers)
    assert res_comm_25.status_code == 201

    # Commercial 500.0 kW succeeds
    res_comm_500 = client.post("/api/v1/enquiries", json={"customer_id": comm_cust_id, "proposed_capacity_kw": 500.0}, headers=headers)
    assert res_comm_500.status_code == 201

    # Commercial > 500.0 kW fails
    res_comm_bad = client.post("/api/v1/enquiries", json={"customer_id": comm_cust_id, "proposed_capacity_kw": 550.0}, headers=headers)
    assert res_comm_bad.status_code in (400, 422)

    # 3. Industrial customer
    res_ind_cust = client.post(
        "/api/v1/customers",
        json={
            "customer_type": "INDUSTRIAL",
            "full_name": f"Industrial Customer {suffix}",
            "phone": f"6{suffix}303"[:10],
            "address": "Industrial Estate Zone 4",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "pincode": "600001",
        },
        headers=headers,
    )
    ind_cust_id = res_ind_cust.json()["data"]["id"]

    # Industrial 100.0 kW succeeds
    res_ind_100 = client.post("/api/v1/enquiries", json={"customer_id": ind_cust_id, "proposed_capacity_kw": 100.0}, headers=headers)
    assert res_ind_100.status_code == 201


def test_dashboard_conversion_calculation(setup_crm_auth_tokens):
    headers = setup_crm_auth_tokens["sales_a"]["headers"]

    res = client.get("/api/v1/crm/dashboard", headers=headers)
    assert res.status_code == 200
    metrics = res.json()["data"]

    total = metrics["total_enquiries"]
    won = metrics["enquiries_by_status"].get("WON", 0)
    expected_rate = round((won / total * 100), 1) if total > 0 else 0.0

    assert metrics["conversion_rate_percentage"] == expected_rate
    assert "CANCELLED" in metrics["enquiries_by_status"]
    assert "LOST" in metrics["enquiries_by_status"]
