from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_
from datetime import datetime, timezone

from app.database import get_db
from app.models.auth import Skill, EmployeeSkill, Employee, User
from app.schemas.skill import (
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    EmployeeSkillAssign,
    EmployeeSkillResponse,
)
from app.schemas import APIResponse
from app.dependencies.auth import get_current_user, require_permissions
from app.utils.roles import SystemRole

router = APIRouter(tags=["Skills Management"])


def _build_skill_response(skill: Skill, db: Session) -> SkillResponse:
    emp_count = db.execute(
        select(func.count(EmployeeSkill.id)).where(EmployeeSkill.skill_id == skill.id)
    ).scalar() or 0

    return SkillResponse(
        id=skill.id,
        name=skill.name,
        category=skill.category,
        description=skill.description,
        is_active=skill.is_active,
        employee_count=emp_count,
        created_at=skill.created_at,
    )


def _build_employee_skill_response(es: EmployeeSkill) -> EmployeeSkillResponse:
    verified_name = None
    if es.verified_by and hasattr(es, "verifier") and es.verifier:
        verified_name = es.verifier.full_name

    return EmployeeSkillResponse(
        id=es.id,
        employee_id=es.employee_id,
        skill_id=es.skill_id,
        skill_name=es.skill.name if es.skill else "",
        skill_category=es.skill.category if es.skill else "",
        proficiency_level=es.proficiency_level,
        years_of_experience=float(es.years_of_experience),
        verified_by=es.verified_by,
        verified_by_name=verified_name,
        verified_at=es.verified_at,
        created_at=es.created_at,
    )


@router.get("/skills", response_model=APIResponse[List[SkillResponse]])
def list_skills(
    category: Optional[str] = Query(None, description="Filter by category (ELECTRICAL, MOUNTING, etc.)"),
    search: Optional[str] = Query(None, description="Search by skill name"),
    is_active: Optional[bool] = Query(None, description="Filter active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("skills.read")),
):
    """
    List available skills with counts of certified/assigned employees.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers are not authorized to view technical skills",
        )

    stmt = select(Skill)
    if category:
        stmt = stmt.where(func.lower(Skill.category) == category.strip().lower())
    if search:
        term = f"%{search.strip().lower()}%"
        stmt = stmt.where(func.lower(Skill.name).like(term))
    if is_active is not None:
        stmt = stmt.where(Skill.is_active == is_active)

    stmt = stmt.order_by(Skill.category.asc(), Skill.name.asc())
    skills = db.execute(stmt).scalars().all()

    items = [_build_skill_response(s, db) for s in skills]
    return APIResponse(
        success=True,
        message="Skills retrieved successfully",
        data=items,
    )


@router.post("/skills", response_model=APIResponse[SkillResponse], status_code=status.HTTP_201_CREATED)
def create_skill(
    payload: SkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("skills.manage")),
):
    """
    Create a new skill in the catalog.
    Restricted to SUPER_ADMIN and TECHNICAL_MANAGER.
    """
    clean_name = payload.name.strip()
    existing = db.execute(
        select(Skill).where(func.lower(Skill.name) == clean_name.lower())
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Skill '{clean_name}' already exists in catalog",
        )

    skill = Skill(
        name=clean_name,
        category=payload.category.strip().upper(),
        description=payload.description.strip() if payload.description else None,
        is_active=payload.is_active,
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)

    return APIResponse(
        success=True,
        message="Skill created successfully",
        data=_build_skill_response(skill, db),
    )


@router.put("/skills/{skill_id}", response_model=APIResponse[SkillResponse])
def update_skill(
    skill_id: int,
    payload: SkillUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("skills.manage")),
):
    """
    Update a skill in the catalog.
    """
    skill = db.execute(select(Skill).where(Skill.id == skill_id)).scalar_one_or_none()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill {skill_id} not found",
        )

    if payload.name is not None:
        clean_name = payload.name.strip()
        dup = db.execute(
            select(Skill).where(
                func.lower(Skill.name) == clean_name.lower(),
                Skill.id != skill_id,
            )
        ).scalar_one_or_none()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Skill name '{clean_name}' is already used",
            )
        skill.name = clean_name

    if payload.category is not None:
        skill.category = payload.category.strip().upper()

    if payload.description is not None:
        skill.description = payload.description.strip()

    if payload.is_active is not None:
        skill.is_active = payload.is_active

    db.commit()
    db.refresh(skill)

    return APIResponse(
        success=True,
        message="Skill updated successfully",
        data=_build_skill_response(skill, db),
    )


@router.get("/employees/{employee_id}/skills", response_model=APIResponse[List[EmployeeSkillResponse]])
def get_employee_skills(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("skills.read")),
):
    """
    Retrieve all skills assigned to a specific employee.
    """
    if current_user.role and current_user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers are not authorized to view employee skills",
        )

    emp = db.execute(select(Employee).where(Employee.id == employee_id)).scalar_one_or_none()
    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found",
        )

    stmt = (
        select(EmployeeSkill)
        .where(EmployeeSkill.employee_id == employee_id)
        .options(selectinload(EmployeeSkill.skill))
        .order_by(EmployeeSkill.created_at.asc())
    )
    assigned_skills = db.execute(stmt).scalars().all()

    items = [_build_employee_skill_response(es) for es in assigned_skills]
    return APIResponse(
        success=True,
        message=f"Skills for employee {employee_id} retrieved",
        data=items,
    )


@router.post("/employees/{employee_id}/skills", response_model=APIResponse[EmployeeSkillResponse], status_code=status.HTTP_201_CREATED)
def assign_skill_to_employee(
    employee_id: int,
    payload: EmployeeSkillAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("skills.manage")),
):
    """
    Assign a skill to an employee.
    Enforces uniqueness (prevents duplicate assignments).
    """
    emp = db.execute(select(Employee).where(Employee.id == employee_id)).scalar_one_or_none()
    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found",
        )

    skill = db.execute(select(Skill).where(Skill.id == payload.skill_id)).scalar_one_or_none()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill {payload.skill_id} not found",
        )

    # Check for existing duplicate assignment
    existing = db.execute(
        select(EmployeeSkill).where(
            EmployeeSkill.employee_id == employee_id,
            EmployeeSkill.skill_id == payload.skill_id,
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Skill '{skill.name}' is already assigned to this employee",
        )

    prof = payload.proficiency_level.upper()
    if prof not in ["BEGINNER", "INTERMEDIATE", "EXPERT"]:
        prof = "INTERMEDIATE"

    verified_by_id = current_user.id if payload.is_verified else None
    verified_at_time = datetime.now(timezone.utc) if payload.is_verified else None

    emp_skill = EmployeeSkill(
        employee_id=employee_id,
        skill_id=payload.skill_id,
        proficiency_level=prof,
        years_of_experience=payload.years_of_experience,
        verified_by=verified_by_id,
        verified_at=verified_at_time,
    )
    db.add(emp_skill)
    db.commit()
    db.refresh(emp_skill)

    # Eager load skill
    emp_skill = db.execute(
        select(EmployeeSkill)
        .where(EmployeeSkill.id == emp_skill.id)
        .options(selectinload(EmployeeSkill.skill))
    ).scalar_one()

    return APIResponse(
        success=True,
        message=f"Skill '{skill.name}' assigned to employee successfully",
        data=_build_employee_skill_response(emp_skill),
    )


@router.delete("/employees/{employee_id}/skills/{skill_id}", response_model=APIResponse[dict])
def remove_skill_from_employee(
    employee_id: int,
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("skills.manage")),
):
    """
    Remove an assigned skill from an employee.
    """
    emp_skill = db.execute(
        select(EmployeeSkill).where(
            EmployeeSkill.employee_id == employee_id,
            EmployeeSkill.skill_id == skill_id,
        )
    ).scalar_one_or_none()

    if not emp_skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill assignment for employee {employee_id} and skill {skill_id} not found",
        )

    db.delete(emp_skill)
    db.commit()

    return APIResponse(
        success=True,
        message="Skill assignment removed successfully",
        data={"employee_id": employee_id, "skill_id": skill_id},
    )
