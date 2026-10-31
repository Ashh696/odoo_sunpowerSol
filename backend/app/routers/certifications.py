from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_, and_
from datetime import date, datetime, timedelta, timezone

from app.database import get_db
from app.models.auth import EmployeeCertification, Employee, User, Department
from app.schemas.certification import (
    CertificationCreate,
    CertificationUpdate,
    CertificationResponse,
)
from app.schemas import APIResponse
from app.dependencies.auth import get_current_user, require_permissions
from app.utils.roles import SystemRole

router = APIRouter(tags=["Certification Management"])


def _build_certification_response(cert: EmployeeCertification) -> CertificationResponse:
    today = date.today()
    is_expired = False
    days_to_expiry = None

    if cert.expiry_date:
        delta = (cert.expiry_date - today).days
        days_to_expiry = delta
        if delta < 0:
            is_expired = True

    emp_name = None
    emp_code = None
    dept_name = None

    if cert.employee:
        emp_code = cert.employee.employee_code
        if cert.employee.user:
            emp_name = cert.employee.user.full_name
        if cert.employee.department:
            dept_name = cert.employee.department.name

    return CertificationResponse(
        id=cert.id,
        employee_id=cert.employee_id,
        employee_code=emp_code,
        employee_name=emp_name,
        department_name=dept_name,
        certification_name=cert.certification_name,
        issuing_authority=cert.issuing_authority,
        certificate_number=cert.certificate_number,
        issue_date=cert.issue_date,
        expiry_date=cert.expiry_date,
        attachment_id=cert.attachment_id,
        verification_status=cert.verification_status,
        is_expired=is_expired,
        days_to_expiry=days_to_expiry,
        created_at=cert.created_at,
        updated_at=cert.updated_at,
    )


@router.get("/employees/{employee_id}/certifications", response_model=APIResponse[List[CertificationResponse]])
def get_employee_certifications(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("certifications.read")),
):
    """
    Retrieve all certifications for an employee.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers are not authorized to view employee certifications",
        )

    emp = db.execute(select(Employee).where(Employee.id == employee_id)).scalar_one_or_none()
    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found",
        )

    stmt = (
        select(EmployeeCertification)
        .where(EmployeeCertification.employee_id == employee_id)
        .options(
            selectinload(EmployeeCertification.employee)
            .selectinload(Employee.user),
            selectinload(EmployeeCertification.employee)
            .selectinload(Employee.department),
        )
        .order_by(EmployeeCertification.issue_date.desc())
    )
    certs = db.execute(stmt).scalars().all()

    items = [_build_certification_response(c) for c in certs]
    return APIResponse(
        success=True,
        message=f"Certifications for employee {employee_id} retrieved",
        data=items,
    )


@router.post("/employees/{employee_id}/certifications", response_model=APIResponse[CertificationResponse], status_code=status.HTTP_201_CREATED)
def add_employee_certification(
    employee_id: int,
    payload: CertificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("certifications.manage")),
):
    """
    Add a new technical or safety certification for an employee.
    """
    emp = db.execute(select(Employee).where(Employee.id == employee_id)).scalar_one_or_none()
    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found",
        )

    # Validate dates
    if payload.expiry_date and payload.expiry_date < payload.issue_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expiry date cannot be earlier than issue date",
        )

    status_val = payload.verification_status.upper()
    if status_val not in ["PENDING", "VERIFIED", "EXPIRED", "REJECTED"]:
        status_val = "PENDING"

    # Auto set EXPIRED if expiry_date in past
    if payload.expiry_date and payload.expiry_date < date.today():
        status_val = "EXPIRED"

    cert = EmployeeCertification(
        employee_id=employee_id,
        certification_name=payload.certification_name.strip(),
        issuing_authority=payload.issuing_authority.strip(),
        certificate_number=payload.certificate_number.strip() if payload.certificate_number else None,
        issue_date=payload.issue_date,
        expiry_date=payload.expiry_date,
        attachment_id=payload.attachment_id,
        verification_status=status_val,
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)

    cert = db.execute(
        select(EmployeeCertification)
        .where(EmployeeCertification.id == cert.id)
        .options(
            selectinload(EmployeeCertification.employee).selectinload(Employee.user),
            selectinload(EmployeeCertification.employee).selectinload(Employee.department),
        )
    ).scalar_one()

    return APIResponse(
        success=True,
        message="Certification recorded successfully",
        data=_build_certification_response(cert),
    )


@router.put("/certifications/{certification_id}", response_model=APIResponse[CertificationResponse])
def update_certification(
    certification_id: int,
    payload: CertificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("certifications.manage")),
):
    """
    Update certification details or verification status.
    """
    cert = db.execute(
        select(EmployeeCertification)
        .where(EmployeeCertification.id == certification_id)
        .options(
            selectinload(EmployeeCertification.employee).selectinload(Employee.user),
            selectinload(EmployeeCertification.employee).selectinload(Employee.department),
        )
    ).scalar_one_or_none()

    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certification {certification_id} not found",
        )

    new_issue = payload.issue_date if payload.issue_date is not None else cert.issue_date
    new_expiry = payload.expiry_date if payload.expiry_date is not None else cert.expiry_date

    if new_expiry and new_issue and new_expiry < new_issue:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expiry date cannot be earlier than issue date",
        )

    if payload.certification_name is not None:
        cert.certification_name = payload.certification_name.strip()
    if payload.issuing_authority is not None:
        cert.issuing_authority = payload.issuing_authority.strip()
    if payload.certificate_number is not None:
        cert.certificate_number = payload.certificate_number.strip()
    if payload.issue_date is not None:
        cert.issue_date = payload.issue_date
    if payload.expiry_date is not None:
        cert.expiry_date = payload.expiry_date
    if payload.attachment_id is not None:
        cert.attachment_id = payload.attachment_id
    if payload.verification_status is not None:
        status_val = payload.verification_status.upper()
        if status_val in ["PENDING", "VERIFIED", "EXPIRED", "REJECTED"]:
            cert.verification_status = status_val

    # Auto check expiration
    if cert.expiry_date and cert.expiry_date < date.today() and cert.verification_status != "REJECTED":
        cert.verification_status = "EXPIRED"

    cert.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(cert)

    return APIResponse(
        success=True,
        message="Certification updated successfully",
        data=_build_certification_response(cert),
    )


@router.get("/certifications/expiring", response_model=APIResponse[List[CertificationResponse]])
def get_expiring_certifications(
    days: int = Query(30, ge=1, le=365, description="Number of days threshold to check upcoming expiry"),
    include_already_expired: bool = Query(True, description="Whether to include past expired certifications"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("certifications.read")),
):
    """
    Identify certifications that are expired or approaching expiry within N days.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers are not authorized to view employee certifications",
        )

    today = date.today()
    future_threshold = today + timedelta(days=days)

    stmt = (
        select(EmployeeCertification)
        .options(
            selectinload(EmployeeCertification.employee).selectinload(Employee.user),
            selectinload(EmployeeCertification.employee).selectinload(Employee.department),
        )
    )

    if include_already_expired:
        stmt = stmt.where(
            and_(
                EmployeeCertification.expiry_date.isnot(None),
                EmployeeCertification.expiry_date <= future_threshold,
            )
        )
    else:
        stmt = stmt.where(
            and_(
                EmployeeCertification.expiry_date.isnot(None),
                EmployeeCertification.expiry_date >= today,
                EmployeeCertification.expiry_date <= future_threshold,
            )
        )

    stmt = stmt.order_by(EmployeeCertification.expiry_date.asc())
    certs = db.execute(stmt).scalars().all()

    items = [_build_certification_response(c) for c in certs]
    return APIResponse(
        success=True,
        message=f"Found {len(items)} expiring/expired certifications within {days} days",
        data=items,
    )
