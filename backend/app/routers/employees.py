from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_, and_
from datetime import date, datetime, timezone
import secrets

from app.database import get_db
from app.models.auth import (
    Employee,
    User,
    Department,
    Role,
    Skill,
    EmployeeSkill,
    EmployeeCertification,
)
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeStatusUpdate,
    EmployeeResponse,
    EmployeeListResponse,
)
from app.schemas.skill import EmployeeSkillResponse
from app.schemas.certification import CertificationResponse
from app.schemas import APIResponse
from app.dependencies.auth import get_current_user, require_permissions
from app.utils.roles import SystemRole
from app.utils.security import hash_password, generate_human_friendly_password, generate_unique_work_email

router = APIRouter(prefix="/employees", tags=["Employee Management"])


def _build_employee_response(emp: Employee) -> EmployeeResponse:
    dept_name = emp.department.name if emp.department else None
    dept_code = emp.department.code if emp.department else None

    user_full_name = ""
    user_email = ""
    user_phone = None
    user_role_slug = None
    user_active = True
    has_login = True

    if emp.user:
        user_full_name = emp.user.full_name
        user_email = emp.user.email
        user_phone = emp.user.phone
        user_active = emp.user.is_active
        if emp.user.role:
            user_role_slug = emp.user.role.slug
        # If user is inactive or has a dummy unguessable password marker, login is not enabled
        if not emp.user.is_active or emp.user.hashed_password.startswith("$disabled$"):
            has_login = False

    # Build skill responses
    skill_items: List[EmployeeSkillResponse] = []
    if hasattr(emp, "skills") and emp.skills:
        for s in emp.skills:
            skill_items.append(
                EmployeeSkillResponse(
                    id=s.id,
                    employee_id=s.employee_id,
                    skill_id=s.skill_id,
                    skill_name=s.skill.name if s.skill else "",
                    skill_category=s.skill.category if s.skill else "",
                    proficiency_level=s.proficiency_level,
                    years_of_experience=float(s.years_of_experience),
                    verified_by=s.verified_by,
                    verified_at=s.verified_at,
                    created_at=s.created_at,
                )
            )

    # Build certification responses
    cert_items: List[CertificationResponse] = []
    if hasattr(emp, "certifications") and emp.certifications:
        today = date.today()
        for c in emp.certifications:
            is_expired = False
            days_to_expiry = None
            if c.expiry_date:
                delta = (c.expiry_date - today).days
                days_to_expiry = delta
                if delta < 0:
                    is_expired = True

            cert_items.append(
                CertificationResponse(
                    id=c.id,
                    employee_id=c.employee_id,
                    employee_code=emp.employee_code,
                    employee_name=user_full_name,
                    department_name=dept_name,
                    certification_name=c.certification_name,
                    issuing_authority=c.issuing_authority,
                    certificate_number=c.certificate_number,
                    issue_date=c.issue_date,
                    expiry_date=c.expiry_date,
                    attachment_id=c.attachment_id,
                    verification_status=c.verification_status,
                    is_expired=is_expired,
                    days_to_expiry=days_to_expiry,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
            )

    return EmployeeResponse(
        id=emp.id,
        employee_code=emp.employee_code,
        designation=emp.designation,
        employment_type=emp.employment_type,
        joining_date=emp.joining_date,
        exit_date=emp.exit_date,
        emergency_contact=emp.emergency_contact,
        is_active=emp.is_active,
        department_id=emp.department_id,
        department_name=dept_name,
        department_code=dept_code,
        user_id=emp.user_id,
        full_name=user_full_name,
        email=user_email,
        phone=user_phone,
        user_role=user_role_slug,
        user_is_active=user_active,
        has_login_access=has_login,
        skills=skill_items,
        certifications=cert_items,
        created_at=emp.created_at,
        updated_at=emp.updated_at,
    )


@router.get("", response_model=APIResponse[EmployeeListResponse])
def list_employees(
    search: Optional[str] = Query(None, description="Search by name, employee code, email, or phone"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    employment_type: Optional[str] = Query(None, description="Filter by FULL_TIME, CONTRACTOR, INTERN"),
    skill_id: Optional[int] = Query(None, description="Filter by assigned skill ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("employees.read")),
):
    """
    List and filter employees with search, department filtering, status, and pagination.
    Accessible to authorized internal staff (Super Admin, Director, Technical Manager, etc.).
    Customer role is strictly forbidden.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers are not authorized to access internal employee directories",
        )

    # Base query joined with User and Department
    stmt = (
        select(Employee)
        .join(User, Employee.user_id == User.id)
        .join(Department, Employee.department_id == Department.id)
        .options(
            selectinload(Employee.user).selectinload(User.role),
            selectinload(Employee.department),
            selectinload(Employee.skills).selectinload(EmployeeSkill.skill),
            selectinload(Employee.certifications),
        )
    )

    if department_id:
        stmt = stmt.where(Employee.department_id == department_id)

    if is_active is not None:
        stmt = stmt.where(Employee.is_active == is_active)

    if employment_type:
        stmt = stmt.where(Employee.employment_type == employment_type.strip().upper())

    if skill_id:
        # Filter employees who possess this skill
        stmt = stmt.where(
            Employee.id.in_(
                select(EmployeeSkill.employee_id).where(EmployeeSkill.skill_id == skill_id)
            )
        )

    if search:
        term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Employee.employee_code).like(term),
                func.lower(Employee.designation).like(term),
                func.lower(User.full_name).like(term),
                func.lower(User.email).like(term),
                func.lower(User.phone).like(term),
            )
        )

    # Count total matching rows
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count = db.execute(count_stmt).scalar() or 0

    # Paginate and order
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
    offset = (page - 1) * page_size
    stmt = stmt.order_by(Employee.is_active.desc(), Employee.employee_code.asc()).offset(offset).limit(page_size)

    employees = db.execute(stmt).scalars().all()
    items = [_build_employee_response(e) for e in employees]

    result = EmployeeListResponse(
        items=items,
        total=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

    return APIResponse(
        success=True,
        message="Employees retrieved successfully",
        data=result,
    )


@router.post("", response_model=APIResponse[EmployeeResponse], status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("employees.manage")),
):
    """
    Create a new employee profile.
    Enforces business rules:
    - User account and employee profile separation.
    - If linking existing user: validates existence, non-customer role, and single employee profile.
    - If user not provided: provisions user record (with or without login account based on create_login_account).
    - Prevents customer accounts from receiving employee profiles.
    - Validates employee_code uniqueness.
    - Validates department exists.
    """
    clean_code = payload.employee_code.strip().upper()

    # 1. Check unique employee code
    dup_code = db.execute(
        select(Employee).where(Employee.employee_code == clean_code)
    ).scalar_one_or_none()
    if dup_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee code '{clean_code}' already exists",
        )

    # 2. Check department
    dept = db.execute(
        select(Department).where(Department.id == payload.department_id)
    ).scalar_one_or_none()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department ID {payload.department_id} not found",
        )

    # 3. Resolve User record
    target_user: User
    if payload.user_id:
        # Linking an existing user
        user = db.execute(
            select(User).where(User.id == payload.user_id).options(selectinload(User.role))
        ).scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User ID {payload.user_id} not found",
            )
        # Business Rule 4: Customer accounts must not receive employee profiles
        if user.role and user.role.slug == SystemRole.CUSTOMER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer accounts cannot be assigned an employee profile",
            )
        # Check if user already has an employee profile
        existing_emp = db.execute(
            select(Employee).where(Employee.user_id == user.id)
        ).scalar_one_or_none()
        if existing_emp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User ID {user.id} ({user.email}) is already linked to employee '{existing_emp.employee_code}'",
            )
        target_user = user
    else:
        # Creating a user record for the employee
        resolved_full_name = (payload.full_name or "").strip()
        if not resolved_full_name and (payload.first_name or payload.last_name):
            resolved_full_name = f"{(payload.first_name or '').strip()} {(payload.last_name or '').strip()}".strip()
        if not resolved_full_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="full_name (or first_name and last_name) is required when not linking an existing user_id",
            )
        if payload.email:
            clean_email = payload.email.lower().strip()
        else:
            fn = payload.first_name or (resolved_full_name.split()[0] if resolved_full_name else "")
            ln = payload.last_name or (resolved_full_name.split()[-1] if len(resolved_full_name.split()) > 1 else "")
            clean_email = generate_unique_work_email(db, fn, ln)



        # Check unique email
        dup_email = db.execute(select(User).where(User.email == clean_email)).scalar_one_or_none()
        if dup_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User email '{clean_email}' already exists in system. Use user_id={dup_email.id} to link.",
            )

        # Check unique phone if provided
        clean_phone = payload.phone.strip() if payload.phone else None
        if clean_phone:
            dup_phone = db.execute(select(User).where(User.phone == clean_phone)).scalar_one_or_none()
            if dup_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Phone number '{clean_phone}' is already registered to another user",
                )

        # Resolve role
        role_slug = payload.role_slug.upper() if payload.role_slug else SystemRole.FIELD_TECHNICIAN
        if role_slug == SystemRole.CUSTOMER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee cannot be created with CUSTOMER role",
            )

        role = db.execute(select(Role).where(Role.slug == role_slug)).scalar_one_or_none()
        if not role:
            # Fallback to FIELD_TECHNICIAN
            role = db.execute(select(Role).where(Role.slug == SystemRole.FIELD_TECHNICIAN)).scalar_one()

        # Handle password and login permission (Business Rules 1 & 2)
        if payload.create_login_account:
            if not payload.password or len(payload.password) < 8:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A password of at least 8 characters is required when provisioning a login account",
                )
            hashed = hash_password(payload.password)
            is_active_user = True
            is_verified = True
        else:
            # Non-login employee profile: set unusable random hash and inactive flag
            hashed = hash_password(secrets.token_urlsafe(32))
            is_active_user = False
            is_verified = False

        new_user = User(
            role_id=role.id,
            email=clean_email,
            phone=clean_phone,
            full_name=resolved_full_name,
            hashed_password=hashed,
            is_active=is_active_user,
            is_verified=is_verified,
        )
        db.add(new_user)
        db.flush()
        target_user = new_user

    # 4. Create Employee record
    emp_type = payload.employment_type.upper() if payload.employment_type else "FULL_TIME"
    if emp_type not in ["FULL_TIME", "CONTRACTOR", "INTERN"]:
        emp_type = "FULL_TIME"

    employee = Employee(
        user_id=target_user.id,
        department_id=payload.department_id,
        employee_code=clean_code,
        designation=payload.designation.strip(),
        employment_type=emp_type,
        joining_date=payload.joining_date,
        emergency_contact=payload.emergency_contact.strip() if payload.emergency_contact else None,
        is_active=True,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)

    # Fetch loaded employee
    stmt = (
        select(Employee)
        .where(Employee.id == employee.id)
        .options(
            selectinload(Employee.user).selectinload(User.role),
            selectinload(Employee.department),
            selectinload(Employee.skills).selectinload(EmployeeSkill.skill),
            selectinload(Employee.certifications),
        )
    )
    loaded_emp = db.execute(stmt).scalar_one()

    return APIResponse(
        success=True,
        message=f"Employee '{loaded_emp.employee_code}' created successfully",
        data=_build_employee_response(loaded_emp),
    )


@router.get("/generate-email", response_model=APIResponse[dict])
def get_generated_work_email(
    first_name: str = Query(..., min_length=1, max_length=100, description="Employee first name"),
    last_name: Optional[str] = Query(None, max_length=100, description="Employee last name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("employees.manage")),
):
    """
    Generate an automatic conflict-free company work email based on employee names.
    Format: firstname.lastname@companydomain
    Appends numeric suffix for duplicates (e.g. firstname.lastname2@companydomain).
    """
    from app.config import settings
    email = generate_unique_work_email(db, first_name=first_name, last_name=last_name or "")
    domain = getattr(settings, "COMPANY_EMAIL_DOMAIN", "sunpower.com")
    return APIResponse(
        success=True,
        message="Generated unique work email address",
        data={
            "email": email,
            "domain": domain,
            "is_mailbox_provisioned": False,
            "note": "SIMS authentication and identity address only. External mailboxes are not provisioned.",
        },
    )


@router.get("/generate-password", response_model=APIResponse[dict])
def get_generated_password(
    current_user: User = Depends(require_permissions("employees.manage")),
):
    """
    Generate a human-friendly temporary password for employee account provisioning.
    Requires employee management privileges (e.g. SUPER_ADMIN).
    """
    generated_pwd = generate_human_friendly_password()
    return APIResponse(
        success=True,
        message="Generated temporary password",
        data={"password": generated_pwd},
    )


@router.get("/{employee_id}", response_model=APIResponse[EmployeeResponse])
def get_employee_details(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("employees.read")),
):
    """
    Retrieve full employee profile, linked user info, assigned skills, and certifications.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers are not authorized to view internal employee details",
        )

    stmt = (
        select(Employee)
        .where(Employee.id == employee_id)
        .options(
            selectinload(Employee.user).selectinload(User.role),
            selectinload(Employee.department),
            selectinload(Employee.skills).selectinload(EmployeeSkill.skill),
            selectinload(Employee.certifications),
        )
    )
    emp = db.execute(stmt).scalar_one_or_none()

    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found",
        )

    return APIResponse(
        success=True,
        message="Employee details retrieved",
        data=_build_employee_response(emp),
    )


@router.put("/{employee_id}", response_model=APIResponse[EmployeeResponse])
def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("employees.manage")),
):
    """
    Update employee information and linked user contact details.
    Restricted to SUPER_ADMIN.
    """
    stmt = (
        select(Employee)
        .where(Employee.id == employee_id)
        .options(
            selectinload(Employee.user).selectinload(User.role),
            selectinload(Employee.department),
            selectinload(Employee.skills).selectinload(EmployeeSkill.skill),
            selectinload(Employee.certifications),
        )
    )
    emp = db.execute(stmt).scalar_one_or_none()

    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found",
        )

    if payload.department_id is not None:
        dept = db.execute(
            select(Department).where(Department.id == payload.department_id)
        ).scalar_one_or_none()
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department {payload.department_id} not found",
            )
        emp.department_id = payload.department_id

    if payload.designation is not None:
        emp.designation = payload.designation.strip()

    if payload.employment_type is not None:
        emp_type = payload.employment_type.upper().strip()
        if emp_type in ["FULL_TIME", "CONTRACTOR", "INTERN"]:
            emp.employment_type = emp_type

    if payload.joining_date is not None:
        emp.joining_date = payload.joining_date

    if payload.exit_date is not None:
        if emp.joining_date and payload.exit_date < emp.joining_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exit date cannot be earlier than joining date",
            )
        emp.exit_date = payload.exit_date

    if payload.emergency_contact is not None:
        emp.emergency_contact = payload.emergency_contact.strip()

    if payload.is_active is not None:
        emp.is_active = payload.is_active

    # Update linked user fields
    if emp.user:
        if payload.full_name is not None:
            emp.user.full_name = payload.full_name.strip()
        if payload.phone is not None:
            clean_phone = payload.phone.strip() if payload.phone else None
            if clean_phone:
                dup_phone = db.execute(
                    select(User).where(User.phone == clean_phone, User.id != emp.user_id)
                ).scalar_one_or_none()
                if dup_phone:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Phone number '{clean_phone}' is already used by another user",
                    )
            emp.user.phone = clean_phone
        if payload.email is not None:
            clean_email = payload.email.lower().strip()
            dup_email = db.execute(
                select(User).where(User.email == clean_email, User.id != emp.user_id)
            ).scalar_one_or_none()
            if dup_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{clean_email}' is already used by another user",
                )
            emp.user.email = clean_email

    emp.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(emp)

    return APIResponse(
        success=True,
        message="Employee information updated successfully",
        data=_build_employee_response(emp),
    )


@router.patch("/{employee_id}/status", response_model=APIResponse[EmployeeResponse])
def toggle_employee_status(
    employee_id: int,
    payload: EmployeeStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("employees.manage")),
):
    """
    Activate or deactivate an employee.
    Preserves historical operational and certification records.
    When deactivating: records exit date (defaults to today if not provided).
    When reactivating: clears exit date.
    """
    stmt = (
        select(Employee)
        .where(Employee.id == employee_id)
        .options(
            selectinload(Employee.user).selectinload(User.role),
            selectinload(Employee.department),
            selectinload(Employee.skills).selectinload(EmployeeSkill.skill),
            selectinload(Employee.certifications),
        )
    )
    emp = db.execute(stmt).scalar_one_or_none()

    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found",
        )

    emp.is_active = payload.is_active

    if not payload.is_active:
        # Deactivating: set exit_date
        exit_d = payload.exit_date if payload.exit_date else date.today()
        if emp.joining_date and exit_d < emp.joining_date:
            exit_d = emp.joining_date
        emp.exit_date = exit_d
        # Also deactivate user login if associated
        if emp.user:
            emp.user.is_active = False
    else:
        # Reactivating: clear exit_date
        emp.exit_date = None
        if emp.user:
            emp.user.is_active = True

    emp.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(emp)

    status_str = "activated" if emp.is_active else "deactivated"
    return APIResponse(
        success=True,
        message=f"Employee '{emp.employee_code}' {status_str} successfully. Historical records preserved.",
        data=_build_employee_response(emp),
    )
