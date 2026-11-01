import pytest
import io
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.database import SessionLocal
from app.models.auth import User, Role, Department, Employee
from app.models.crm import Customer, Enquiry, Survey, SurveyApproval
from app.utils.security import hash_password, create_access_token
from app.utils.roles import SystemRole

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_survey_auth():
    """
    Provision authenticated users, employees, and tokens across roles:
    - Super Admin
    - Director
    - Technical Manager
    - Field Technician A & B
    - Sales Representative A & B
    - Customer
    """
    with SessionLocal() as db:
        admin_role = db.execute(select(Role).where(Role.slug == SystemRole.SUPER_ADMIN)).scalar_one()
        dir_role = db.execute(select(Role).where(Role.slug == SystemRole.DIRECTOR)).scalar_one()
        tm_role = db.execute(select(Role).where(Role.slug == SystemRole.TECHNICAL_MANAGER)).scalar_one()
        ft_role = db.execute(select(Role).where(Role.slug == SystemRole.FIELD_TECHNICIAN)).scalar_one()
        sales_role = db.execute(select(Role).where(Role.slug == SystemRole.SALES)).scalar_one()
        cust_role = db.execute(select(Role).where(Role.slug == SystemRole.CUSTOMER)).scalar_one()

        dept = db.execute(select(Department).where(Department.is_active == True)).scalars().first()
        if not dept:
            dept = Department(name="Technical Surveys", code="TECH_SURV")
            db.add(dept)
            db.commit()
            db.refresh(dept)

        # 1. Admin
        admin_user = db.execute(select(User).where(User.email == "srv_admin@sunpower.com")).scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                role_id=admin_role.id,
                email="srv_admin@sunpower.com",
                full_name="Survey Admin",
                hashed_password=hash_password("AdminPass123!"),
                is_active=True,
                is_verified=True,
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

        # 2. Director
        director_user = db.execute(select(User).where(User.email == "srv_director@sunpower.com")).scalar_one_or_none()
        if not director_user:
            director_user = User(
                role_id=dir_role.id,
                email="srv_director@sunpower.com",
                full_name="Survey Director",
                hashed_password=hash_password("DirectorPass123!"),
                is_active=True,
                is_verified=True,
            )
            db.add(director_user)
            db.commit()
            db.refresh(director_user)

        # 3. Technical Manager
        tm_user = db.execute(select(User).where(User.email == "srv_tm@sunpower.com")).scalar_one_or_none()
        if not tm_user:
            tm_user = User(
                role_id=tm_role.id,
                email="srv_tm@sunpower.com",
                full_name="Tech Manager Terry",
                hashed_password=hash_password("TechManager123!"),
                is_active=True,
                is_verified=True,
            )
            db.add(tm_user)
            db.commit()
            db.refresh(tm_user)

        # 4. Field Technician A
        ft_a_user = db.execute(select(User).where(User.email == "srv_tech_a@sunpower.com")).scalar_one_or_none()
        if not ft_a_user:
            ft_a_user = User(
                role_id=ft_role.id,
                email="srv_tech_a@sunpower.com",
                full_name="Field Tech Andy",
                hashed_password=hash_password("TechPass123!"),
                is_active=True,
                is_verified=True,
            )
            db.add(ft_a_user)
            db.commit()
            db.refresh(ft_a_user)

        ft_a_emp = db.execute(select(Employee).where(Employee.user_id == ft_a_user.id)).scalar_one_or_none()
        if not ft_a_emp:
            ft_a_emp = Employee(
                user_id=ft_a_user.id,
                department_id=dept.id,
                employee_code="EMP-TECH-A",
                designation="Field Technician A",
                employment_type="FULL_TIME",
                joining_date=datetime.now(timezone.utc).date(),
                is_active=True,
            )
            db.add(ft_a_emp)
            db.commit()
            db.refresh(ft_a_emp)

        # 5. Field Technician B
        ft_b_user = db.execute(select(User).where(User.email == "srv_tech_b@sunpower.com")).scalar_one_or_none()
        if not ft_b_user:
            ft_b_user = User(
                role_id=ft_role.id,
                email="srv_tech_b@sunpower.com",
                full_name="Field Tech Brian",
                hashed_password=hash_password("TechPass123!"),
                is_active=True,
                is_verified=True,
            )
            db.add(ft_b_user)
            db.commit()
            db.refresh(ft_b_user)

        ft_b_emp = db.execute(select(Employee).where(Employee.user_id == ft_b_user.id)).scalar_one_or_none()
        if not ft_b_emp:
            ft_b_emp = Employee(
                user_id=ft_b_user.id,
                department_id=dept.id,
                employee_code="EMP-TECH-B",
                designation="Field Technician B",
                employment_type="FULL_TIME",
                joining_date=datetime.now(timezone.utc).date(),
                is_active=True,
            )
            db.add(ft_b_emp)
            db.commit()
            db.refresh(ft_b_emp)

        # 6. Inactive Technician
        ft_inact_user = db.execute(select(User).where(User.email == "srv_tech_inact@sunpower.com")).scalar_one_or_none()
        if not ft_inact_user:
            ft_inact_user = User(
                role_id=ft_role.id,
                email="srv_tech_inact@sunpower.com",
                full_name="Inactive Technician",
                hashed_password=hash_password("TechPass123!"),
                is_active=False,
                is_verified=True,
            )
            db.add(ft_inact_user)
            db.commit()
            db.refresh(ft_inact_user)

        ft_inact_emp = db.execute(select(Employee).where(Employee.user_id == ft_inact_user.id)).scalar_one_or_none()
        if not ft_inact_emp:
            ft_inact_emp = Employee(
                user_id=ft_inact_user.id,
                department_id=dept.id,
                employee_code="EMP-TECH-INACT",
                designation="Inactive Technician",
                employment_type="FULL_TIME",
                joining_date=datetime.now(timezone.utc).date(),
                is_active=False,
            )
            db.add(ft_inact_emp)
            db.commit()
            db.refresh(ft_inact_emp)

        # 7. Sales Rep A
        sales_a_user = db.execute(select(User).where(User.email == "srv_sales_a@sunpower.com")).scalar_one_or_none()
        if not sales_a_user:
            sales_a_user = User(
                role_id=sales_role.id,
                email="srv_sales_a@sunpower.com",
                full_name="Sales Alice",
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
                employee_code="EMP-SRV-SALES-A",
                designation="Sales Representative A",
                employment_type="FULL_TIME",
                joining_date=datetime.now(timezone.utc).date(),
                is_active=True,
            )
            db.add(sales_a_emp)
            db.commit()
            db.refresh(sales_a_emp)

        # 8. Sales Rep B
        sales_b_user = db.execute(select(User).where(User.email == "srv_sales_b@sunpower.com")).scalar_one_or_none()
        if not sales_b_user:
            sales_b_user = User(
                role_id=sales_role.id,
                email="srv_sales_b@sunpower.com",
                full_name="Sales Bob",
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
                employee_code="EMP-SRV-SALES-B",
                designation="Sales Representative B",
                employment_type="FULL_TIME",
                joining_date=datetime.now(timezone.utc).date(),
                is_active=True,
            )
            db.add(sales_b_emp)
            db.commit()
            db.refresh(sales_b_emp)

        # 9. Customer
        cust_user = db.execute(select(User).where(User.email == "srv_customer@sunpower.com")).scalar_one_or_none()
        if not cust_user:
            cust_user = User(
                role_id=cust_role.id,
                email="srv_customer@sunpower.com",
                full_name="Survey Customer",
                hashed_password=hash_password("CustPass123!"),
                is_active=True,
                is_verified=True,
            )
            db.add(cust_user)
            db.commit()
            db.refresh(cust_user)

        admin_token = create_access_token({"sub": str(admin_user.id), "email": admin_user.email, "role": admin_role.slug})
        dir_token = create_access_token({"sub": str(director_user.id), "email": director_user.email, "role": dir_role.slug})
        tm_token = create_access_token({"sub": str(tm_user.id), "email": tm_user.email, "role": tm_role.slug})
        tech_a_token = create_access_token({"sub": str(ft_a_user.id), "email": ft_a_user.email, "role": ft_role.slug})
        tech_b_token = create_access_token({"sub": str(ft_b_user.id), "email": ft_b_user.email, "role": ft_role.slug})
        sales_a_token = create_access_token({"sub": str(sales_a_user.id), "email": sales_a_user.email, "role": sales_role.slug})
        sales_b_token = create_access_token({"sub": str(sales_b_user.id), "email": sales_b_user.email, "role": sales_role.slug})
        cust_token = create_access_token({"sub": str(cust_user.id), "email": cust_user.email, "role": cust_role.slug})

        return {
            "admin": {"headers": {"Authorization": f"Bearer {admin_token}"}},
            "director": {"headers": {"Authorization": f"Bearer {dir_token}"}},
            "tm": {"headers": {"Authorization": f"Bearer {tm_token}"}},
            "tech_a": {"employee_id": ft_a_emp.id, "headers": {"Authorization": f"Bearer {tech_a_token}"}},
            "tech_b": {"employee_id": ft_b_emp.id, "headers": {"Authorization": f"Bearer {tech_b_token}"}},
            "tech_inact_emp_id": ft_inact_emp.id,
            "sales_a": {"employee_id": sales_a_emp.id, "headers": {"Authorization": f"Bearer {sales_a_token}"}},
            "sales_b": {"employee_id": sales_b_emp.id, "headers": {"Authorization": f"Bearer {sales_b_token}"}},
            "customer": {"headers": {"Authorization": f"Bearer {cust_token}"}},
        }


def _create_test_enquiry(headers, sales_emp_id, customer_type="RESIDENTIAL", capacity_kw=3.0):
    suffix = uuid.uuid4().hex[:6]
    res_c = client.post(
        "/api/v1/customers",
        json={
            "customer_type": customer_type,
            "full_name": f"Survey Cust {suffix}",
            "phone": f"9{suffix}123"[:10],
            "address": "123 Solar Street",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560001",
        },
        headers=headers,
    )
    assert res_c.status_code == 201
    cust_id = res_c.json()["data"]["id"]

    res_e = client.post(
        "/api/v1/enquiries",
        json={
            "customer_id": cust_id,
            "proposed_capacity_kw": capacity_kw,
            "assigned_sales_id": sales_emp_id,
            "notes": "Qualified lead ready for site survey",
        },
        headers=headers,
    )
    assert res_e.status_code == 201
    return res_e.json()["data"]["id"]


# ==========================================
# 1. SURVEY SCHEDULING & AUTHORIZATION
# ==========================================

def test_survey_scheduling_and_permissions(setup_survey_auth):
    auth = setup_survey_auth
    sales_a = auth["sales_a"]
    sales_b = auth["sales_b"]
    tech_a = auth["tech_a"]
    cust = auth["customer"]
    tm = auth["tm"]

    enq_a_id = _create_test_enquiry(sales_a["headers"], sales_a["employee_id"])

    # 1. FIELD_TECHNICIAN cannot schedule surveys
    res_ft_sched = client.post(
        "/api/v1/surveys",
        json={"enquiry_id": enq_a_id, "surveyor_id": tech_a["employee_id"], "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()},
        headers=tech_a["headers"],
    )
    assert res_ft_sched.status_code == 403

    # 2. CUSTOMER cannot schedule surveys
    res_cust_sched = client.post(
        "/api/v1/surveys",
        json={"enquiry_id": enq_a_id, "surveyor_id": tech_a["employee_id"], "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()},
        headers=cust["headers"],
    )
    assert res_cust_sched.status_code == 403

    # 3. SALES Rep B cannot schedule survey for Rep A's enquiry
    res_b_sched = client.post(
        "/api/v1/surveys",
        json={"enquiry_id": enq_a_id, "surveyor_id": tech_a["employee_id"], "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()},
        headers=sales_b["headers"],
    )
    assert res_b_sched.status_code == 403

    # 4. Inactive surveyor assignment is rejected
    res_inact_sched = client.post(
        "/api/v1/surveys",
        json={"enquiry_id": enq_a_id, "surveyor_id": auth["tech_inact_emp_id"], "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()},
        headers=sales_a["headers"],
    )
    assert res_inact_sched.status_code == 400
    assert "inactive" in res_inact_sched.json()["detail"].lower()

    # 5. SALES Rep A successfully schedules survey for own enquiry
    res_sched = client.post(
        "/api/v1/surveys",
        json={
            "enquiry_id": enq_a_id,
            "surveyor_id": tech_a["employee_id"],
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            "remarks": "Check roof shading and tilt angle",
        },
        headers=sales_a["headers"],
    )
    assert res_sched.status_code == 201
    survey_data = res_sched.json()["data"]
    assert survey_data["status"] == "DRAFT"
    assert survey_data["surveyor_id"] == tech_a["employee_id"]
    srv_num = survey_data["survey_number"]
    assert srv_num.startswith("SRV-")
    parts = srv_num.split("-")
    assert len(parts) == 3
    assert len(parts[1]) == 8
    assert len(parts[2]) == 4

    # Enquiry status transitioned to SURVEY_REQUESTED
    res_enq_check = client.get(f"/api/v1/enquiries/{enq_a_id}", headers=sales_a["headers"])
    assert res_enq_check.status_code == 200
    assert res_enq_check.json()["data"]["status"] == "SURVEY_REQUESTED"

    # 6. Duplicate active survey prevention
    res_dup = client.post(
        "/api/v1/surveys",
        json={"enquiry_id": enq_a_id, "surveyor_id": tech_a["employee_id"], "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()},
        headers=tm["headers"],
    )
    assert res_dup.status_code == 400
    assert "already exists" in res_dup.json()["detail"].lower()


# ==========================================
# 2. SURVEY NUMBER CONCURRENCY RETRY
# ==========================================

def test_survey_number_concurrency_and_retry(setup_survey_auth, monkeypatch):
    auth = setup_survey_auth
    tm = auth["tm"]
    tech_a = auth["tech_a"]
    sales_a = auth["sales_a"]

    enq_id = _create_test_enquiry(sales_a["headers"], sales_a["employee_id"])

    # 1. Normal creation
    res_normal = client.post(
        "/api/v1/surveys",
        json={"enquiry_id": enq_id, "surveyor_id": tech_a["employee_id"], "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()},
        headers=tm["headers"],
    )
    assert res_normal.status_code == 201
    existing_srv_num = res_normal.json()["data"]["survey_number"]

    # 2. Simulate collision retry on another enquiry
    enq_id_2 = _create_test_enquiry(sales_a["headers"], sales_a["employee_id"])

    import app.routers.surveys as srv_module
    original_gen = srv_module._generate_survey_number
    collision_tracker = {"calls": 0}

    def mock_gen(db):
        collision_tracker["calls"] += 1
        if collision_tracker["calls"] == 1:
            # Duplicate key collision triggers real IntegrityError
            return existing_srv_num
        return original_gen(db)

    monkeypatch.setattr(srv_module, "_generate_survey_number", mock_gen)

    res_retry = client.post(
        "/api/v1/surveys",
        json={"enquiry_id": enq_id_2, "surveyor_id": tech_a["employee_id"], "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()},
        headers=tm["headers"],
    )
    assert res_retry.status_code == 201
    assert collision_tracker["calls"] == 2
    assert res_retry.json()["data"]["survey_number"] != existing_srv_num

    # 3. Exhausted retries -> 409 Conflict
    enq_id_3 = _create_test_enquiry(sales_a["headers"], sales_a["employee_id"])
    monkeypatch.setattr(srv_module, "_generate_survey_number", lambda db: existing_srv_num)

    res_exhausted = client.post(
        "/api/v1/surveys",
        json={"enquiry_id": enq_id_3, "surveyor_id": tech_a["employee_id"], "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()},
        headers=tm["headers"],
    )
    assert res_exhausted.status_code == 409
    assert "Unable to generate a unique survey number" in res_exhausted.json()["detail"]

    # 4. Unrelated IntegrityErrors are not retried as collisions
    from sqlalchemy.exc import IntegrityError
    def mock_commit_foreign_key_fail():
        raise IntegrityError("insert into surveys ... foreign key constraint violation", params={}, orig=Exception("fk_violation"))

    enq_id_4 = _create_test_enquiry(sales_a["headers"], sales_a["employee_id"])
    monkeypatch.setattr(srv_module, "_generate_survey_number", original_gen)

    # Monkeypatch db.commit within create attempt to raise unrelated IntegrityError
    from sqlalchemy.orm import Session
    orig_commit = Session.commit
    fail_tracker = {"calls": 0}
    def mock_db_commit(self):
        fail_tracker["calls"] += 1
        raise IntegrityError("FOREIGN KEY constraint failed on foreign table", params={}, orig=Exception("fk_constraint"))

    monkeypatch.setattr(Session, "commit", mock_db_commit)
    res_unrelated_err = client.post(
        "/api/v1/surveys",
        json={"enquiry_id": enq_id_4, "surveyor_id": tech_a["employee_id"], "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()},
        headers=tm["headers"],
    )
    monkeypatch.setattr(Session, "commit", orig_commit)
    assert res_unrelated_err.status_code == 400
    assert "Database integrity conflict" in res_unrelated_err.json()["detail"]
    # Verify it stopped on attempt 1 without retrying
    assert fail_tracker["calls"] == 1


# ==========================================
# 3. SURVEYOR DATA ISOLATION & ACCESS CONTROL
# ==========================================

def test_surveyor_data_isolation(setup_survey_auth):
    auth = setup_survey_auth
    tm = auth["tm"]
    tech_a = auth["tech_a"]
    tech_b = auth["tech_b"]
    sales_a = auth["sales_a"]
    sales_b = auth["sales_b"]
    cust = auth["customer"]

    enq_a = _create_test_enquiry(sales_a["headers"], sales_a["employee_id"])
    res_srv_a = client.post(
        "/api/v1/surveys",
        json={"enquiry_id": enq_a, "surveyor_id": tech_a["employee_id"], "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()},
        headers=tm["headers"],
    )
    srv_a_id = res_srv_a.json()["data"]["id"]

    # 1. Tech A can view survey A
    res_tech_a_get = client.get(f"/api/v1/surveys/{srv_a_id}", headers=tech_a["headers"])
    assert res_tech_a_get.status_code == 200

    # 2. Tech B cannot view Tech A's survey (403)
    res_tech_b_get = client.get(f"/api/v1/surveys/{srv_a_id}", headers=tech_b["headers"])
    assert res_tech_b_get.status_code == 403

    # 3. Tech B listing does not include Tech A's survey
    res_tech_b_list = client.get("/api/v1/surveys", headers=tech_b["headers"])
    assert res_tech_b_list.status_code == 200
    b_ids = [s["id"] for s in res_tech_b_list.json()["data"]["items"]]
    assert srv_a_id not in b_ids

    # 4. Tech B cannot filter by Tech A's ID
    res_tech_b_filter = client.get(f"/api/v1/surveys?surveyor_id={tech_a['employee_id']}", headers=tech_b["headers"])
    assert res_tech_b_filter.status_code == 403

    # 5. Sales Rep A can view survey A; Sales Rep B is rejected
    assert client.get(f"/api/v1/surveys/{srv_a_id}", headers=sales_a["headers"]).status_code == 200
    assert client.get(f"/api/v1/surveys/{srv_a_id}", headers=sales_b["headers"]).status_code == 403

    # 6. Customer receives 403
    assert client.get(f"/api/v1/surveys/{srv_a_id}", headers=cust["headers"]).status_code == 403


# ==========================================
# 4. MEASUREMENT VALIDATION & SUBMISSION
# ==========================================

def test_survey_measurements_and_submission(setup_survey_auth):
    auth = setup_survey_auth
    tm = auth["tm"]
    tech_a = auth["tech_a"]
    tech_b = auth["tech_b"]
    sales_a = auth["sales_a"]

    enq_id = _create_test_enquiry(sales_a["headers"], sales_a["employee_id"])
    res_srv = client.post(
        "/api/v1/surveys",
        json={"enquiry_id": enq_id, "surveyor_id": tech_a["employee_id"], "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()},
        headers=tm["headers"],
    )
    srv_id = res_srv.json()["data"]["id"]

    # 1. Tech B cannot update Tech A's survey
    res_bad_tech = client.put(f"/api/v1/surveys/{srv_id}", json={"roof_area_sqft": 500}, headers=tech_b["headers"])
    assert res_bad_tech.status_code == 403

    # 2. Invalid measurements: shadow free area > roof area
    res_bad_area = client.put(
        f"/api/v1/surveys/{srv_id}",
        json={"roof_area_sqft": 400.0, "shadow_free_area_sqft": 450.0},
        headers=tech_a["headers"],
    )
    assert res_bad_area.status_code == 400
    assert "cannot exceed total roof area" in res_bad_area.json()["detail"]

    # 3. Invalid GPS latitude
    res_bad_lat = client.put(f"/api/v1/surveys/{srv_id}", json={"gps_latitude": 95.0}, headers=tech_a["headers"])
    assert res_bad_lat.status_code == 422  # Pydantic validation error

    # 4. Invalid tilt angle
    res_bad_tilt = client.put(f"/api/v1/surveys/{srv_id}", json={"roof_tilt_degrees": 95.0}, headers=tech_a["headers"])
    assert res_bad_tilt.status_code == 422

    # 5. DRAFT survey cannot be approved before submission
    res_bad_app = client.post(f"/api/v1/surveys/{srv_id}/review", json={"action": "APPROVED", "comments": "Premature approval"}, headers=tm["headers"])
    assert res_bad_app.status_code == 400
    assert "must be submitted" in res_bad_app.json()["detail"].lower()

    # 6. Premature submission missing observations
    res_pre_sub = client.put(f"/api/v1/surveys/{srv_id}/submit", headers=tech_a["headers"])
    assert res_pre_sub.status_code == 400
    assert "missing required technical observations" in res_pre_sub.json()["detail"]

    # 7. Valid observation recording
    res_valid_upd = client.put(
        f"/api/v1/surveys/{srv_id}",
        json={
            "roof_area_sqft": 600.0,
            "shadow_free_area_sqft": 520.0,
            "roof_orientation": "SOUTH",
            "roof_tilt_degrees": 15.0,
            "roof_structure_type": "FLUSH",
            "existing_phase": "SINGLE_PHASE",
            "sanctioned_load_kw": 5.0,
            "gps_latitude": 12.9716,
            "gps_longitude": 77.5946,
            "technical_feasibility": "FEASIBLE",
            "remarks": "Solid RCC roof structure, excellent solar access",
        },
        headers=tech_a["headers"],
    )
    assert res_valid_upd.status_code == 200
    assert res_valid_upd.json()["data"]["roof_area_sqft"] == 600.0

    # 8. Successful submission
    res_submit = client.put(f"/api/v1/surveys/{srv_id}/submit", headers=tech_a["headers"])
    assert res_submit.status_code == 200
    assert res_submit.json()["data"]["status"] == "SUBMITTED"
    assert res_submit.json()["data"]["conducted_at"] is not None


# ==========================================
# 5. TECHNICAL REVIEW, CORRECTIONS & LIFECYCLE
# ==========================================

def test_survey_approval_correction_and_rejection_cycle(setup_survey_auth):
    auth = setup_survey_auth
    tm = auth["tm"]
    director = auth["director"]
    tech_a = auth["tech_a"]
    sales_a = auth["sales_a"]

    enq_id = _create_test_enquiry(sales_a["headers"], sales_a["employee_id"])
    res_srv = client.post(
        "/api/v1/surveys",
        json={"enquiry_id": enq_id, "surveyor_id": tech_a["employee_id"], "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()},
        headers=tm["headers"],
    )
    srv_id = res_srv.json()["data"]["id"]

    # Record technical observations
    client.put(
        f"/api/v1/surveys/{srv_id}",
        json={
            "roof_area_sqft": 500.0,
            "shadow_free_area_sqft": 400.0,
            "roof_orientation": "SOUTH",
            "roof_tilt_degrees": 12.0,
            "roof_structure_type": "ELEVATED",
            "existing_phase": "THREE_PHASE",
            "sanctioned_load_kw": 10.0,
            "technical_feasibility": "FEASIBLE",
        },
        headers=tech_a["headers"],
    )
    # Submit survey
    client.put(f"/api/v1/surveys/{srv_id}/submit", headers=tech_a["headers"])

    # 1. Field technician cannot review
    assert client.post(f"/api/v1/surveys/{srv_id}/review", json={"action": "APPROVED", "comments": "Self approval"}, headers=tech_a["headers"]).status_code == 403

    # 2. Sales rep cannot review
    assert client.post(f"/api/v1/surveys/{srv_id}/review", json={"action": "APPROVED", "comments": "Sales approval"}, headers=sales_a["headers"]).status_code == 403

    # 3. Decision CORRECTION_REQUESTED requires meaningful comments
    res_short = client.post(f"/api/v1/surveys/{srv_id}/review", json={"action": "CORRECTION_REQUESTED", "comments": "no"}, headers=tm["headers"])
    assert res_short.status_code == 400

    # 4. Technical Manager requests corrections (Revision 1)
    res_corr = client.post(
        f"/api/v1/surveys/{srv_id}/review",
        json={"action": "CORRECTION_REQUESTED", "comments": "Please double check the east parapet wall shadow impact"},
        headers=tm["headers"],
    )
    assert res_corr.status_code == 200
    detail = res_corr.json()["data"]
    assert detail["status"] == "CORRECTION_REQUESTED"
    assert len(detail["approvals"]) == 1
    assert detail["approvals"][0]["revision_number"] == 1
    assert detail["approvals"][0]["action"] == "CORRECTION_REQUESTED"

    # 5. Surveyor updates observations based on feedback
    res_upd = client.put(
        f"/api/v1/surveys/{srv_id}",
        json={"shadow_free_area_sqft": 360.0, "remarks": "Adjusted shadow-free area for parapet wall morning shadow"},
        headers=tech_a["headers"],
    )
    assert res_upd.status_code == 200
    assert res_upd.json()["data"]["shadow_free_area_sqft"] == 360.0

    # 6. Surveyor resubmits
    res_resub = client.put(f"/api/v1/surveys/{srv_id}/submit", headers=tech_a["headers"])
    assert res_resub.status_code == 200
    assert res_resub.json()["data"]["status"] == "SUBMITTED"

    # 7. Director grants technical approval (Revision 2)
    res_app = client.post(
        f"/api/v1/surveys/{srv_id}/review",
        json={"action": "APPROVED", "comments": "Shadow profiling verified. Approved for quotation engineering."},
        headers=director["headers"],
    )
    assert res_app.status_code == 200
    app_detail = res_app.json()["data"]
    assert app_detail["status"] == "APPROVED"
    assert len(app_detail["approvals"]) == 2
    assert app_detail["approvals"][1]["revision_number"] == 2
    assert app_detail["approvals"][1]["action"] == "APPROVED"

    # 8. Approved survey cannot be edited
    res_edit_app = client.put(f"/api/v1/surveys/{srv_id}", json={"roof_area_sqft": 550.0}, headers=tech_a["headers"])
    assert res_edit_app.status_code == 400

    # 9. Parent enquiry status remains SURVEY_REQUESTED as approved
    res_enq_check = client.get(f"/api/v1/enquiries/{enq_id}", headers=sales_a["headers"])
    assert res_enq_check.json()["data"]["status"] == "SURVEY_REQUESTED"

    # 10. REJECTED lifecycle & cannot be silently resubmitted or edited
    enq_rej_id = _create_test_enquiry(sales_a["headers"], sales_a["employee_id"])
    res_srv_rej = client.post(
        "/api/v1/surveys",
        json={"enquiry_id": enq_rej_id, "surveyor_id": tech_a["employee_id"], "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()},
        headers=tm["headers"],
    )
    srv_rej_id = res_srv_rej.json()["data"]["id"]
    client.put(
        f"/api/v1/surveys/{srv_rej_id}",
        json={
            "roof_area_sqft": 100.0,
            "shadow_free_area_sqft": 50.0,
            "roof_orientation": "NORTH",
            "existing_phase": "SINGLE_PHASE",
            "technical_feasibility": "NOT_FEASIBLE",
        },
        headers=tech_a["headers"],
    )
    client.put(f"/api/v1/surveys/{srv_rej_id}/submit", headers=tech_a["headers"])

    # Reject survey
    res_rej = client.post(
        f"/api/v1/surveys/{srv_rej_id}/review",
        json={"action": "REJECTED", "comments": "Rooftop structure is decaying asbestos; site is unsafe for solar."},
        headers=tm["headers"],
    )
    assert res_rej.status_code == 200
    assert res_rej.json()["data"]["status"] == "REJECTED"

    # REJECTED survey cannot be edited
    assert client.put(f"/api/v1/surveys/{srv_rej_id}", json={"roof_area_sqft": 200.0}, headers=tech_a["headers"]).status_code == 400

    # REJECTED survey cannot be resubmitted
    assert client.put(f"/api/v1/surveys/{srv_rej_id}/submit", headers=tech_a["headers"]).status_code == 400


# ==========================================
# 6. ATTACHMENT UPLOAD & AUTHORIZATION
# ==========================================

def test_survey_file_attachments(setup_survey_auth):
    auth = setup_survey_auth
    tm = auth["tm"]
    tech_a = auth["tech_a"]
    tech_b = auth["tech_b"]
    sales_a = auth["sales_a"]

    enq_id = _create_test_enquiry(sales_a["headers"], sales_a["employee_id"])
    res_srv = client.post(
        "/api/v1/surveys",
        json={"enquiry_id": enq_id, "surveyor_id": tech_a["employee_id"], "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()},
        headers=tm["headers"],
    )
    srv_id = res_srv.json()["data"]["id"]

    # 1. Tech B cannot upload attachment to Tech A's survey
    fake_photo = io.BytesIO(b"fake image data")
    res_b_upload = client.post(
        f"/api/v1/surveys/{srv_id}/attachments",
        files={"file": ("roof_photo.jpg", fake_photo, "image/jpeg")},
        headers=tech_b["headers"],
    )
    assert res_b_upload.status_code == 403

    # 2. Reject executable or invalid file formats
    fake_exe = io.BytesIO(b"malicious script")
    res_bad_ext = client.post(
        f"/api/v1/surveys/{srv_id}/attachments",
        files={"file": ("hack.exe", fake_exe, "application/octet-stream")},
        headers=tech_a["headers"],
    )
    assert res_bad_ext.status_code == 400
    assert "Invalid file type" in res_bad_ext.json()["detail"]

    # 3. Valid photo upload by assigned surveyor
    valid_photo = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF sample roof site image bytes")
    res_upload = client.post(
        f"/api/v1/surveys/{srv_id}/attachments",
        files={"file": ("site_shadow_layout.jpg", valid_photo, "image/jpeg")},
        headers=tech_a["headers"],
    )
    assert res_upload.status_code == 201
    att_data = res_upload.json()["data"]
    assert att_data["entity_type"] == "SURVEY"
    assert att_data["entity_id"] == srv_id
    assert att_data["file_name"] == "site_shadow_layout.jpg"

    # 4. List attachments
    res_att_list = client.get(f"/api/v1/surveys/{srv_id}/attachments", headers=tech_a["headers"])
    assert res_att_list.status_code == 200
    items = res_att_list.json()["data"]
    assert len(items) == 1
    assert items[0]["file_name"] == "site_shadow_layout.jpg"
