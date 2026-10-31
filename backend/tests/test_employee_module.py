import pytest
import uuid
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.database import SessionLocal
from app.models.auth import User, Role, Department, Employee, Skill, EmployeeSkill, EmployeeCertification
from app.utils.roles import SystemRole
from app.utils.security import hash_password, create_access_token

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_auth_tokens():
    db = SessionLocal()
    try:
        # Fetch canonical roles
        sa_role = db.execute(select(Role).where(Role.slug == SystemRole.SUPER_ADMIN)).scalar_one()
        dir_role = db.execute(select(Role).where(Role.slug == SystemRole.DIRECTOR)).scalar_one()
        tech_role = db.execute(select(Role).where(Role.slug == SystemRole.TECHNICAL_MANAGER)).scalar_one()
        cust_role = db.execute(select(Role).where(Role.slug == SystemRole.CUSTOMER)).scalar_one()

        # 1. Super Admin User
        admin_user = db.execute(select(User).where(User.email == "module_admin@sunpower.com")).scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                role_id=sa_role.id,
                email="module_admin@sunpower.com",
                full_name="Module Super Admin",
                hashed_password=hash_password("AdminPass123!"),
                is_active=True,
                is_verified=True,
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

        # 2. Director User
        director_user = db.execute(select(User).where(User.email == "module_director@sunpower.com")).scalar_one_or_none()
        if not director_user:
            director_user = User(
                role_id=dir_role.id,
                email="module_director@sunpower.com",
                full_name="Module Director",
                hashed_password=hash_password("DirectorPass123!"),
                is_active=True,
                is_verified=True,
            )
            db.add(director_user)
            db.commit()
            db.refresh(director_user)

        # 3. Technical Manager User
        tech_user = db.execute(select(User).where(User.email == "module_tech@sunpower.com")).scalar_one_or_none()
        if not tech_user:
            tech_user = User(
                role_id=tech_role.id,
                email="module_tech@sunpower.com",
                full_name="Module Tech Manager",
                hashed_password=hash_password("TechPass123!"),
                is_active=True,
                is_verified=True,
            )
            db.add(tech_user)
            db.commit()
            db.refresh(tech_user)

        # 4. Customer User
        cust_user = db.execute(select(User).where(User.email == "module_customer@sunpower.com")).scalar_one_or_none()
        if not cust_user:
            cust_user = User(
                role_id=cust_role.id,
                email="module_customer@sunpower.com",
                full_name="Module Customer",
                hashed_password=hash_password("CustPass123!"),
                is_active=True,
                is_verified=True,
            )
            db.add(cust_user)
            db.commit()
            db.refresh(cust_user)

        admin_token = create_access_token({"sub": str(admin_user.id), "email": admin_user.email, "role": sa_role.slug})
        director_token = create_access_token({"sub": str(director_user.id), "email": director_user.email, "role": dir_role.slug})
        tech_token = create_access_token({"sub": str(tech_user.id), "email": tech_user.email, "role": tech_role.slug})
        cust_token = create_access_token({"sub": str(cust_user.id), "email": cust_user.email, "role": cust_role.slug})

        return {
            "admin": {"headers": {"Authorization": f"Bearer {admin_token}"}, "user_id": admin_user.id},
            "director": {"headers": {"Authorization": f"Bearer {director_token}"}, "user_id": director_user.id},
            "tech": {"headers": {"Authorization": f"Bearer {tech_token}"}, "user_id": tech_user.id},
            "customer": {"headers": {"Authorization": f"Bearer {cust_token}"}, "user_id": cust_user.id},
        }
    finally:
        db.close()


def test_department_crud_and_manager_assignment(setup_auth_tokens):
    headers = setup_auth_tokens["admin"]["headers"]
    cust_headers = setup_auth_tokens["customer"]["headers"]
    dir_headers = setup_auth_tokens["director"]["headers"]
    admin_id = setup_auth_tokens["admin"]["user_id"]
    cust_id = setup_auth_tokens["customer"]["user_id"]

    # 1. Customer rejected
    res = client.get("/api/v1/departments", headers=cust_headers)
    assert res.status_code == 403

    # 2. Create Department
    code = f"TEST_{uuid.uuid4().hex[:6].upper()}"
    res = client.post(
        "/api/v1/departments",
        json={"name": f"Dept {code}", "code": code, "manager_id": admin_id},
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()["data"]
    dept_id = data["id"]
    assert data["code"] == code
    assert data["manager_id"] == admin_id

    # 3. Reject customer as manager
    res_bad = client.post(
        "/api/v1/departments",
        json={"name": f"Bad Dept {code}", "code": f"B{code}", "manager_id": cust_id},
        headers=headers,
    )
    assert res_bad.status_code == 400

    # 4. Director can read
    res_dir = client.get(f"/api/v1/departments/{dept_id}", headers=dir_headers)
    assert res_dir.status_code == 200
    assert res_dir.json()["data"]["name"] == f"Dept {code}"

    # 5. Update Department
    res_up = client.put(
        f"/api/v1/departments/{dept_id}",
        json={"name": f"Updated Dept {code}"},
        headers=headers,
    )
    assert res_up.status_code == 200
    assert res_up.json()["data"]["name"] == f"Updated Dept {code}"


def test_employee_crud_and_lifecycle(setup_auth_tokens):
    admin_headers = setup_auth_tokens["admin"]["headers"]
    dir_headers = setup_auth_tokens["director"]["headers"]
    cust_headers = setup_auth_tokens["customer"]["headers"]

    # Get a department ID
    depts_res = client.get("/api/v1/departments", headers=admin_headers)
    assert depts_res.status_code == 200
    dept_id = depts_res.json()["data"][0]["id"]

    emp_code = f"TST-{uuid.uuid4().hex[:5].upper()}"
    emp_email = f"{emp_code.lower()}@testsunpower.com"

    # 1. Customer rejected
    res_cust = client.get("/api/v1/employees", headers=cust_headers)
    assert res_cust.status_code == 403

    # 2. Create Employee
    res = client.post(
        "/api/v1/employees",
        json={
            "employee_code": emp_code,
            "department_id": dept_id,
            "designation": "Lead Solar Technician",
            "employment_type": "FULL_TIME",
            "joining_date": "2026-01-15",
            "emergency_contact": "+91 9876543210",
            "full_name": f"Test Technician {emp_code}",
            "email": emp_email,
            "phone": f"+91 {emp_code[4:]}123456",
            "role_slug": "FIELD_TECHNICIAN",
            "create_login_account": True,
            "password": "Password123!",
        },
        headers=admin_headers,
    )
    assert res.status_code == 201
    emp_data = res.json()["data"]
    emp_id = emp_data["id"]
    assert emp_data["employee_code"] == emp_code
    assert emp_data["is_active"] is True
    assert emp_data["has_login_access"] is True

    # 3. Prevent duplicate employee code
    res_dup = client.post(
        "/api/v1/employees",
        json={
            "employee_code": emp_code,
            "department_id": dept_id,
            "designation": "Duplicate Tech",
            "joining_date": "2026-01-15",
            "full_name": "Duplicate Name",
            "email": f"dup_{emp_email}",
        },
        headers=admin_headers,
    )
    assert res_dup.status_code == 400

    # 4. Director can read employee list & detail
    res_list = client.get(f"/api/v1/employees?search={emp_code}", headers=dir_headers)
    assert res_list.status_code == 200
    assert res_list.json()["data"]["total"] >= 1

    res_detail = client.get(f"/api/v1/employees/{emp_id}", headers=dir_headers)
    assert res_detail.status_code == 200
    assert res_detail.json()["data"]["id"] == emp_id

    # 5. Update employee
    res_up = client.put(
        f"/api/v1/employees/{emp_id}",
        json={"designation": "Senior Lead Solar Technician"},
        headers=admin_headers,
    )
    assert res_up.status_code == 200
    assert res_up.json()["data"]["designation"] == "Senior Lead Solar Technician"

    # 6. Deactivate employee (Soft Deactivation preserving historical data)
    res_deact = client.patch(
        f"/api/v1/employees/{emp_id}/status",
        json={"is_active": False, "exit_date": "2026-10-31"},
        headers=admin_headers,
    )
    assert res_deact.status_code == 200
    assert res_deact.json()["data"]["is_active"] is False
    assert res_deact.json()["data"]["exit_date"] == "2026-10-31"

    # 7. Reactivate employee
    res_act = client.patch(
        f"/api/v1/employees/{emp_id}/status",
        json={"is_active": True},
        headers=admin_headers,
    )
    assert res_act.status_code == 200
    assert res_act.json()["data"]["is_active"] is True
    assert res_act.json()["data"]["exit_date"] is None


def test_skills_management_and_duplicate_prevention(setup_auth_tokens):
    admin_headers = setup_auth_tokens["admin"]["headers"]
    tech_headers = setup_auth_tokens["tech"]["headers"]
    cust_headers = setup_auth_tokens["customer"]["headers"]

    # 1. Customer rejected
    res = client.get("/api/v1/skills", headers=cust_headers)
    assert res.status_code == 403

    # 2. Create Skill
    skill_title = f"High Voltage Inverter Config {uuid.uuid4().hex[:5]}"
    res_skill = client.post(
        "/api/v1/skills",
        json={
            "name": skill_title,
            "category": "ELECTRICAL",
            "description": "Commissioning 3-phase high voltage solar grid inverters",
        },
        headers=tech_headers,
    )
    assert res_skill.status_code == 201
    skill_id = res_skill.json()["data"]["id"]

    # 3. Create a test employee
    depts_res = client.get("/api/v1/departments", headers=admin_headers)
    dept_id = depts_res.json()["data"][0]["id"]
    code = f"SKL-{uuid.uuid4().hex[:5].upper()}"
    res_emp = client.post(
        "/api/v1/employees",
        json={
            "employee_code": code,
            "department_id": dept_id,
            "designation": "Solar Electrician",
            "joining_date": "2026-02-01",
            "full_name": f"Electrician {code}",
            "email": f"{code.lower()}@sunpower.com",
        },
        headers=admin_headers,
    )
    assert res_emp.status_code == 201
    emp_id = res_emp.json()["data"]["id"]

    # 4. Assign skill to employee
    res_assign = client.post(
        f"/api/v1/employees/{emp_id}/skills",
        json={
            "skill_id": skill_id,
            "proficiency_level": "EXPERT",
            "years_of_experience": 4.5,
            "is_verified": True,
        },
        headers=tech_headers,
    )
    assert res_assign.status_code == 201
    assert res_assign.json()["data"]["proficiency_level"] == "EXPERT"
    assert res_assign.json()["data"]["years_of_experience"] == 4.5

    # 5. Prevent duplicate skill assignment
    res_assign_dup = client.post(
        f"/api/v1/employees/{emp_id}/skills",
        json={"skill_id": skill_id, "proficiency_level": "BEGINNER"},
        headers=tech_headers,
    )
    assert res_assign_dup.status_code == 400

    # 6. Retrieve employee skills
    res_emp_skills = client.get(f"/api/v1/employees/{emp_id}/skills", headers=admin_headers)
    assert res_emp_skills.status_code == 200
    assert len(res_emp_skills.json()["data"]) == 1

    # 7. Remove assigned skill
    res_del = client.delete(f"/api/v1/employees/{emp_id}/skills/{skill_id}", headers=tech_headers)
    assert res_del.status_code == 200

    res_emp_skills_after = client.get(f"/api/v1/employees/{emp_id}/skills", headers=admin_headers)
    assert len(res_emp_skills_after.json()["data"]) == 0


def test_certifications_management_and_expiry_tracking(setup_auth_tokens):
    admin_headers = setup_auth_tokens["admin"]["headers"]
    tech_headers = setup_auth_tokens["tech"]["headers"]

    # Create employee
    depts_res = client.get("/api/v1/departments", headers=admin_headers)
    dept_id = depts_res.json()["data"][0]["id"]
    code = f"CRT-{uuid.uuid4().hex[:5].upper()}"
    res_emp = client.post(
        "/api/v1/employees",
        json={
            "employee_code": code,
            "department_id": dept_id,
            "designation": "Rooftop Safety Officer",
            "joining_date": "2026-03-01",
            "full_name": f"Safety Officer {code}",
            "email": f"{code.lower()}@sunpower.com",
        },
        headers=admin_headers,
    )
    assert res_emp.status_code == 201
    emp_id = res_emp.json()["data"]["id"]

    today = date.today()

    # 1. Add Valid Certification
    res_cert1 = client.post(
        f"/api/v1/employees/{emp_id}/certifications",
        json={
            "certification_name": "Working at Heights Level 2",
            "issuing_authority": "National Safety Council",
            "certificate_number": f"NSC-{code}",
            "issue_date": (today - timedelta(days=180)).isoformat(),
            "expiry_date": (today + timedelta(days=20)).isoformat(),  # Expiring in 20 days!
            "verification_status": "VERIFIED",
        },
        headers=tech_headers,
    )
    assert res_cert1.status_code == 201
    cert1 = res_cert1.json()["data"]
    assert cert1["days_to_expiry"] == 20
    assert cert1["is_expired"] is False

    # 2. Add Already Expired Certification
    res_cert2 = client.post(
        f"/api/v1/employees/{emp_id}/certifications",
        json={
            "certification_name": "Basic Electrical Safety 2025",
            "issuing_authority": "State Electrical Inspectorate",
            "certificate_number": f"SEI-{code}",
            "issue_date": (today - timedelta(days=400)).isoformat(),
            "expiry_date": (today - timedelta(days=10)).isoformat(),  # Expired 10 days ago!
            "verification_status": "PENDING",
        },
        headers=tech_headers,
    )
    assert res_cert2.status_code == 201
    cert2 = res_cert2.json()["data"]
    assert cert2["is_expired"] is True
    assert cert2["verification_status"] == "EXPIRED"

    # 3. Reject invalid dates (expiry < issue)
    res_bad_dates = client.post(
        f"/api/v1/employees/{emp_id}/certifications",
        json={
            "certification_name": "Invalid Date Certificate",
            "issuing_authority": "Test",
            "issue_date": "2026-06-01",
            "expiry_date": "2026-01-01",
        },
        headers=tech_headers,
    )
    assert res_bad_dates.status_code == 400

    # 4. Query expiring certifications (30 day threshold)
    res_expiring = client.get("/api/v1/certifications/expiring?days=30", headers=admin_headers)
    assert res_expiring.status_code == 200
    expiring_items = res_expiring.json()["data"]
    # Should include both cert1 (expiring in 20 days) and cert2 (expired 10 days ago)
    cert_ids = [c["id"] for c in expiring_items]
    assert cert1["id"] in cert_ids
    assert cert2["id"] in cert_ids


def test_security_review_no_default_passwords_and_provisioning(setup_auth_tokens):
    """
    Review Area 4: Verify that no default passwords are created.
    Creating a login account without a password or with a password under 8 characters
    must be strictly rejected with HTTP 400.
    """
    admin_headers = setup_auth_tokens["admin"]["headers"]
    depts_res = client.get("/api/v1/departments", headers=admin_headers)
    dept_id = depts_res.json()["data"][0]["id"]
    code = f"SEC-{uuid.uuid4().hex[:5].upper()}"

    # 1. create_login_account=True without password -> Must fail with 400
    res_no_pass = client.post(
        "/api/v1/employees",
        json={
            "employee_code": f"{code}A",
            "department_id": dept_id,
            "designation": "Solar Technician",
            "joining_date": "2026-01-01",
            "full_name": "No Password Test",
            "email": f"{code.lower()}a@sunpower.com",
            "create_login_account": True,
            "password": None,
        },
        headers=admin_headers,
    )
    assert res_no_pass.status_code == 400
    assert "password" in res_no_pass.json()["detail"].lower()

    # 2. create_login_account=True with short password (< 8 chars) -> Must fail with 422/400
    res_short_pass = client.post(
        "/api/v1/employees",
        json={
            "employee_code": f"{code}B",
            "department_id": dept_id,
            "designation": "Solar Technician",
            "joining_date": "2026-01-01",
            "full_name": "Short Password Test",
            "email": f"{code.lower()}b@sunpower.com",
            "create_login_account": True,
            "password": "123",
        },
        headers=admin_headers,
    )
    assert res_short_pass.status_code in [400, 422]

    # 3. Customer role cannot be specified as employee role
    res_cust_role = client.post(
        "/api/v1/employees",
        json={
            "employee_code": f"{code}C",
            "department_id": dept_id,
            "designation": "Customer Employee Attempt",
            "joining_date": "2026-01-01",
            "full_name": "Customer Role Attempt",
            "email": f"{code.lower()}c@sunpower.com",
            "role_slug": "CUSTOMER",
            "create_login_account": True,
            "password": "ValidPassword123!",
        },
        headers=admin_headers,
    )
    assert res_cust_role.status_code == 400
    assert "customer" in res_cust_role.json()["detail"].lower()

    # 4. Valid creation with explicit password succeeds and does not expose password
    res_valid = client.post(
        "/api/v1/employees",
        json={
            "employee_code": f"{code}D",
            "department_id": dept_id,
            "designation": "Solar Technician",
            "joining_date": "2026-01-01",
            "full_name": "Valid Password Test",
            "email": f"{code.lower()}d@sunpower.com",
            "create_login_account": True,
            "password": "SecurePassword123!",
        },
        headers=admin_headers,
    )
    assert res_valid.status_code == 201
    emp_data = res_valid.json()["data"]
    assert "password" not in emp_data
    assert "hashed_password" not in emp_data
    assert emp_data["has_login_access"] is True


def test_security_review_employee_granular_permissions(setup_auth_tokens):
    """
    Review Area 3: Verify explicit backend permission enforcement for:
    - Employee listing.
    - Employee creation.
    - Employee updates.
    - Employee deactivation.
    - Employee reactivation.
    - Employee details.
    Director has `employees.read` but NOT `employees.manage`.
    """
    admin_headers = setup_auth_tokens["admin"]["headers"]
    dir_headers = setup_auth_tokens["director"]["headers"]
    cust_headers = setup_auth_tokens["customer"]["headers"]

    depts_res = client.get("/api/v1/departments", headers=admin_headers)
    dept_id = depts_res.json()["data"][0]["id"]
    code = f"PRM-{uuid.uuid4().hex[:5].upper()}"

    # 1. Director has `employees.read` -> can list and read details
    res_dir_list = client.get("/api/v1/employees", headers=dir_headers)
    assert res_dir_list.status_code == 200

    # 2. Customer has NO employee permissions -> 403 Forbidden
    res_cust_list = client.get("/api/v1/employees", headers=cust_headers)
    assert res_cust_list.status_code == 403

    # 3. Director lacks `employees.manage` -> create employee rejected with 403
    res_dir_create = client.post(
        "/api/v1/employees",
        json={
            "employee_code": code,
            "department_id": dept_id,
            "designation": "Unauthorized Creation",
            "joining_date": "2026-01-01",
            "full_name": "Unauthorized Attempt",
            "email": f"{code.lower()}@sunpower.com",
        },
        headers=dir_headers,
    )
    assert res_dir_create.status_code == 403
    assert "permission" in res_dir_create.json()["detail"].lower()

    # Create employee with Super Admin (who has `employees.manage`)
    res_admin_create = client.post(
        "/api/v1/employees",
        json={
            "employee_code": code,
            "department_id": dept_id,
            "designation": "Authorized Creation",
            "joining_date": "2026-01-01",
            "full_name": "Authorized User",
            "email": f"{code.lower()}@sunpower.com",
        },
        headers=admin_headers,
    )
    assert res_admin_create.status_code == 201
    emp_id = res_admin_create.json()["data"]["id"]

    # 4. Director can read details
    res_dir_detail = client.get(f"/api/v1/employees/{emp_id}", headers=dir_headers)
    assert res_dir_detail.status_code == 200

    # 5. Director lacks `employees.manage` -> update rejected with 403
    res_dir_update = client.put(
        f"/api/v1/employees/{emp_id}",
        json={"designation": "Hacked Designation"},
        headers=dir_headers,
    )
    assert res_dir_update.status_code == 403

    # 6. Director lacks `employees.manage` -> status toggle rejected with 403
    res_dir_deact = client.patch(
        f"/api/v1/employees/{emp_id}/status",
        json={"is_active": False},
        headers=dir_headers,
    )
    assert res_dir_deact.status_code == 403


def test_security_review_certification_permissions(setup_auth_tokens):
    """
    Review Area 2: Verify certification permissions:
    - Director has `certifications.read` but NOT `certifications.manage`.
    - Customer has NO certification permissions (HTTP 403).
    - Creation and verification require `certifications.manage`.
    """
    admin_headers = setup_auth_tokens["admin"]["headers"]
    dir_headers = setup_auth_tokens["director"]["headers"]
    cust_headers = setup_auth_tokens["customer"]["headers"]
    tech_headers = setup_auth_tokens["tech"]["headers"]

    # Create employee for test
    depts_res = client.get("/api/v1/departments", headers=admin_headers)
    dept_id = depts_res.json()["data"][0]["id"]
    code = f"CPRM-{uuid.uuid4().hex[:5].upper()}"
    res_emp = client.post(
        "/api/v1/employees",
        json={
            "employee_code": code,
            "department_id": dept_id,
            "designation": "Solar Tech",
            "joining_date": "2026-01-01",
            "full_name": "Cert Perms Test",
            "email": f"{code.lower()}@sunpower.com",
        },
        headers=admin_headers,
    )
    assert res_emp.status_code == 201
    emp_id = res_emp.json()["data"]["id"]

    # 1. Customer cannot view certifications -> 403
    res_cust = client.get(f"/api/v1/employees/{emp_id}/certifications", headers=cust_headers)
    assert res_cust.status_code == 403

    # 2. Director cannot create certification -> 403 (missing certifications.manage)
    res_dir_create = client.post(
        f"/api/v1/employees/{emp_id}/certifications",
        json={
            "certification_name": "Unauthorized Cert",
            "issuing_authority": "Directorate",
            "issue_date": "2026-01-01",
        },
        headers=dir_headers,
    )
    assert res_dir_create.status_code == 403

    # 3. Technical Manager HAS `certifications.manage` -> Can create certification
    res_tech_create = client.post(
        f"/api/v1/employees/{emp_id}/certifications",
        json={
            "certification_name": "Valid Solar Technical Cert",
            "issuing_authority": "National Solar Energy Institute",
            "issue_date": "2026-01-01",
            "verification_status": "PENDING",
        },
        headers=tech_headers,
    )
    assert res_tech_create.status_code == 201
    cert_id = res_tech_create.json()["data"]["id"]

    # 4. Director cannot verify/update certification -> 403
    res_dir_verify = client.put(
        f"/api/v1/certifications/{cert_id}",
        json={"verification_status": "VERIFIED"},
        headers=dir_headers,
    )
    assert res_dir_verify.status_code == 403

    # 5. Technical Manager CAN verify certification
    res_tech_verify = client.put(
        f"/api/v1/certifications/{cert_id}",
        json={"verification_status": "VERIFIED"},
        headers=tech_headers,
    )
    assert res_tech_verify.status_code == 200
    assert res_tech_verify.json()["data"]["verification_status"] == "VERIFIED"


def test_security_review_inactive_account_login_rejection(setup_auth_tokens):
    """
    Review Area 4: Verify inactive accounts cannot authenticate or access endpoints.
    """
    admin_headers = setup_auth_tokens["admin"]["headers"]
    depts_res = client.get("/api/v1/departments", headers=admin_headers)
    dept_id = depts_res.json()["data"][0]["id"]
    code = f"INACT-{uuid.uuid4().hex[:5].upper()}"
    emp_email = f"{code.lower()}@sunpower.com"
    emp_pass = "ActiveLoginPass123!"

    # 1. Create employee with login account
    res_emp = client.post(
        "/api/v1/employees",
        json={
            "employee_code": code,
            "department_id": dept_id,
            "designation": "Technician To Inactive",
            "joining_date": "2026-01-01",
            "full_name": "Inactive Account Test",
            "email": emp_email,
            "create_login_account": True,
            "password": emp_pass,
        },
        headers=admin_headers,
    )
    assert res_emp.status_code == 201
    emp_id = res_emp.json()["data"]["id"]

    # 2. Login while active -> Succeeds
    res_login = client.post(
        "/api/v1/auth/login",
        json={"email": emp_email, "password": emp_pass},
    )
    assert res_login.status_code == 200
    user_token = res_login.json()["data"]["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 3. Deactivate employee (which deactivates linked user account)
    res_deact = client.patch(
        f"/api/v1/employees/{emp_id}/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert res_deact.status_code == 200

    # 4. Inactive user tries to log in -> HTTP 403 Forbidden
    res_login_inactive = client.post(
        "/api/v1/auth/login",
        json={"email": emp_email, "password": emp_pass},
    )
    assert res_login_inactive.status_code == 403
    assert "inactive" in res_login_inactive.json()["detail"].lower()

    # 5. Existing token for deactivated account is rejected on protected endpoints -> 403
    res_auth_check = client.get("/api/v1/auth/me", headers=user_headers)
    assert res_auth_check.status_code == 403
    assert "inactive" in res_auth_check.json()["detail"].lower()


def test_security_review_historical_preservation(setup_auth_tokens):
    """
    Review Area 5: Verify historical records are preserved on employee deactivation:
    - Employee record is never deleted.
    - Linked user record is never deleted.
    - Employee skills and certifications remain completely intact in DB.
    """
    admin_headers = setup_auth_tokens["admin"]["headers"]
    tech_headers = setup_auth_tokens["tech"]["headers"]

    depts_res = client.get("/api/v1/departments", headers=admin_headers)
    dept_id = depts_res.json()["data"][0]["id"]
    code = f"HIST-{uuid.uuid4().hex[:5].upper()}"

    # 1. Create Employee
    res_emp = client.post(
        "/api/v1/employees",
        json={
            "employee_code": code,
            "department_id": dept_id,
            "designation": "Senior Preservation Engineer",
            "joining_date": "2026-01-01",
            "full_name": "History Test",
            "email": f"{code.lower()}@sunpower.com",
            "create_login_account": True,
            "password": "Password123!",
        },
        headers=admin_headers,
    )
    assert res_emp.status_code == 201
    emp_id = res_emp.json()["data"]["id"]
    user_id = res_emp.json()["data"]["user_id"]

    # 2. Add Skill
    skills_res = client.get("/api/v1/skills", headers=admin_headers)
    skill_id = skills_res.json()["data"][0]["id"]
    res_skill = client.post(
        f"/api/v1/employees/{emp_id}/skills",
        json={"skill_id": skill_id, "proficiency_level": "EXPERT", "years_of_experience": 5.0},
        headers=tech_headers,
    )
    assert res_skill.status_code == 201

    # 3. Add Certification
    res_cert = client.post(
        f"/api/v1/employees/{emp_id}/certifications",
        json={
            "certification_name": "Historical Master Electrician",
            "issuing_authority": "Solar Board",
            "issue_date": "2026-01-01",
            "verification_status": "VERIFIED",
        },
        headers=tech_headers,
    )
    assert res_cert.status_code == 201
    cert_id = res_cert.json()["data"]["id"]

    # 4. Deactivate employee
    res_deact = client.patch(
        f"/api/v1/employees/{emp_id}/status",
        json={"is_active": False, "exit_date": "2026-10-31"},
        headers=admin_headers,
    )
    assert res_deact.status_code == 200

    # 5. Verify records still exist directly in DB session
    db = SessionLocal()
    try:
        emp_in_db = db.execute(select(Employee).where(Employee.id == emp_id)).scalar_one_or_none()
        assert emp_in_db is not None
        assert emp_in_db.is_active is False
        assert str(emp_in_db.exit_date) == "2026-10-31"

        user_in_db = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        assert user_in_db is not None
        assert user_in_db.is_active is False

        # Verify skill assignment still exists in DB
        skill_in_db = db.execute(
            select(EmployeeSkill).where(EmployeeSkill.employee_id == emp_id, EmployeeSkill.skill_id == skill_id)
        ).scalar_one_or_none()
        assert skill_in_db is not None

        # Verify certification still exists in DB
        cert_in_db = db.execute(
            select(EmployeeCertification).where(EmployeeCertification.id == cert_id)
        ).scalar_one_or_none()
        assert cert_in_db is not None
        assert cert_in_db.verification_status == "VERIFIED"
    finally:
        db.close()

    # 6. Details endpoint still accessible to authorized users
    res_details = client.get(f"/api/v1/employees/{emp_id}", headers=admin_headers)
    assert res_details.status_code == 200
    details = res_details.json()["data"]
    assert details["is_active"] is False
    assert len(details["skills"]) >= 1
    assert len(details["certifications"]) >= 1
