from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_
from datetime import datetime, timezone

from app.database import get_db
from app.models.auth import Department, User, Employee
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentDetailResponse,
)
from app.schemas.employee import EmployeeResponse
from app.schemas import APIResponse
from app.dependencies.auth import get_current_user, require_permissions
from app.utils.roles import SystemRole

router = APIRouter(prefix="/departments", tags=["Department Management"])


def _build_department_response(dept: Department, db: Session) -> DepartmentResponse:
    # Compute active employee count
    emp_count = db.execute(
        select(func.count(Employee.id)).where(Employee.department_id == dept.id)
    ).scalar() or 0

    manager_name = None
    manager_email = None
    if dept.manager:
        manager_name = dept.manager.full_name
        manager_email = dept.manager.email

    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        code=dept.code,
        manager_id=dept.manager_id,
        manager_name=manager_name,
        manager_email=manager_email,
        is_active=dept.is_active,
        employee_count=emp_count,
        created_at=dept.created_at,
        updated_at=dept.updated_at,
    )


@router.get("", response_model=APIResponse[List[DepartmentResponse]])
def list_departments(
    search: Optional[str] = Query(None, description="Search by name or code"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("departments.read")),
):
    """
    List all departments with manager details and employee counts.
    Accessible to all internal roles (Customer role rejected).
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers are not authorized to view internal departments",
        )

    stmt = select(Department).options(selectinload(Department.manager))

    if search:
        term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Department.name).like(term),
                func.lower(Department.code).like(term),
            )
        )

    if is_active is not None:
        stmt = stmt.where(Department.is_active == is_active)

    stmt = stmt.order_by(Department.name.asc())
    depts = db.execute(stmt).scalars().all()

    items = [_build_department_response(d, db) for d in depts]
    return APIResponse(
        success=True,
        message="Departments retrieved successfully",
        data=items,
    )


@router.post("", response_model=APIResponse[DepartmentResponse], status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("departments.manage")),
):
    """
    Create a new department.
    Restricted to SUPER_ADMIN.
    """
    clean_name = payload.name.strip()
    clean_code = payload.code.strip().upper()

    # Check unique name and code
    existing = db.execute(
        select(Department).where(
            or_(
                func.lower(Department.name) == clean_name.lower(),
                Department.code == clean_code,
            )
        )
    ).scalar_one_or_none()

    if existing:
        if existing.code == clean_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department code '{clean_code}' already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department name '{clean_name}' already exists",
        )

    # Validate manager_id if supplied
    if payload.manager_id is not None:
        mgr = db.execute(select(User).where(User.id == payload.manager_id)).scalar_one_or_none()
        if not mgr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User ID {payload.manager_id} for manager not found",
            )
        if mgr.role and mgr.role.slug == SystemRole.CUSTOMER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer accounts cannot be assigned as department managers",
            )

    dept = Department(
        name=clean_name,
        code=clean_code,
        manager_id=payload.manager_id,
        is_active=payload.is_active,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)

    # Eager load manager
    dept = db.execute(
        select(Department).where(Department.id == dept.id).options(selectinload(Department.manager))
    ).scalar_one()

    return APIResponse(
        success=True,
        message="Department created successfully",
        data=_build_department_response(dept, db),
    )


@router.get("/{department_id}", response_model=APIResponse[DepartmentResponse])
def get_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("departments.read")),
):
    """
    Retrieve single department details.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers are not authorized to view internal departments",
        )

    dept = db.execute(
        select(Department)
        .where(Department.id == department_id)
        .options(selectinload(Department.manager))
    ).scalar_one_or_none()

    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department {department_id} not found",
        )

    return APIResponse(
        success=True,
        message="Department details retrieved",
        data=_build_department_response(dept, db),
    )


@router.put("/{department_id}", response_model=APIResponse[DepartmentResponse])
def update_department(
    department_id: int,
    payload: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("departments.manage")),
):
    """
    Update department details or assign manager.
    Restricted to SUPER_ADMIN.
    """
    dept = db.execute(
        select(Department)
        .where(Department.id == department_id)
        .options(selectinload(Department.manager))
    ).scalar_one_or_none()

    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department {department_id} not found",
        )

    if payload.name is not None:
        clean_name = payload.name.strip()
        dup = db.execute(
            select(Department).where(
                func.lower(Department.name) == clean_name.lower(),
                Department.id != department_id,
            )
        ).scalar_one_or_none()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department name '{clean_name}' is already used by another department",
            )
        dept.name = clean_name

    if payload.code is not None:
        clean_code = payload.code.strip().upper()
        dup = db.execute(
            select(Department).where(
                Department.code == clean_code,
                Department.id != department_id,
            )
        ).scalar_one_or_none()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department code '{clean_code}' is already used by another department",
            )
        dept.code = clean_code

    if payload.manager_id is not None:
        if payload.manager_id == 0:
            dept.manager_id = None
        else:
            mgr = db.execute(select(User).where(User.id == payload.manager_id)).scalar_one_or_none()
            if not mgr:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User ID {payload.manager_id} for manager not found",
                )
            if mgr.role and mgr.role.slug == SystemRole.CUSTOMER:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Customer accounts cannot be assigned as department managers",
                )
            dept.manager_id = payload.manager_id

    if payload.is_active is not None:
        dept.is_active = payload.is_active

    dept.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(dept)

    dept = db.execute(
        select(Department).where(Department.id == dept.id).options(selectinload(Department.manager))
    ).scalar_one()

    return APIResponse(
        success=True,
        message="Department updated successfully",
        data=_build_department_response(dept, db),
    )


@router.get("/{department_id}/employees", response_model=APIResponse[List[dict]])
def get_department_employees(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("departments.read")),
):
    """
    List all employees belonging to a specific department.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers are not authorized to view internal employees",
        )

    dept = db.execute(select(Department).where(Department.id == department_id)).scalar_one_or_none()
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department {department_id} not found",
        )

    stmt = (
        select(Employee)
        .where(Employee.department_id == department_id)
        .options(selectinload(Employee.user).selectinload(User.role))
        .order_by(Employee.employee_code.asc())
    )
    employees = db.execute(stmt).scalars().all()

    data = [
        {
            "id": emp.id,
            "employee_code": emp.employee_code,
            "designation": emp.designation,
            "employment_type": emp.employment_type,
            "joining_date": emp.joining_date.isoformat() if emp.joining_date else None,
            "is_active": emp.is_active,
            "user_id": emp.user_id,
            "full_name": emp.user.full_name if emp.user else "",
            "email": emp.user.email if emp.user else "",
            "phone": emp.user.phone if emp.user else None,
            "user_role": emp.user.role.slug if emp.user and emp.user.role else None,
        }
        for emp in employees
    ]

    return APIResponse(
        success=True,
        message=f"Employees for department '{dept.name}' retrieved",
        data=data,
    )
