from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class SkillCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Skill title, e.g. Solar Panel Installation")
    category: str = Field(..., min_length=2, max_length=100, description="Category: ELECTRICAL, MOUNTING, SAFETY, COMMISSIONING, etc.")
    description: Optional[str] = None
    is_active: bool = True


class SkillUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SkillResponse(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None
    is_active: bool
    employee_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class EmployeeSkillAssign(BaseModel):
    skill_id: int
    proficiency_level: str = Field("INTERMEDIATE", description="BEGINNER, INTERMEDIATE, or EXPERT")
    years_of_experience: float = Field(0.0, ge=0.0, description="Years of hands-on experience with this skill")
    is_verified: bool = Field(False, description="Whether skill is verified by manager")


class EmployeeSkillResponse(BaseModel):
    id: int
    employee_id: int
    skill_id: int
    skill_name: str
    skill_category: str
    proficiency_level: str
    years_of_experience: float
    verified_by: Optional[int] = None
    verified_by_name: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
