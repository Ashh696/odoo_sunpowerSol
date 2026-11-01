from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from datetime import date, datetime
from app.schemas.skill import EmployeeSkillResponse
from app.schemas.certification import CertificationResponse


class EmployeeCreate(BaseModel):
    employee_code: str = Field(..., min_length=2, max_length=50, description="Unique code, e.g. EMP-001")
    department_id: int = Field(..., description="ID of assigned department")
    designation: str = Field(..., min_length=2, max_length=100)
    employment_type: str = Field("FULL_TIME", description="FULL_TIME, CONTRACTOR, INTERN")
    joining_date: date
    emergency_contact: Optional[str] = Field(None, max_length=100)
    
    # User linking / provisioning options
    user_id: Optional[int] = Field(None, description="Link an existing non-customer user")
    # If user_id is not provided, specify user profile fields:
    full_name: Optional[str] = Field(None, max_length=255)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=30)
    role_slug: Optional[str] = Field("FIELD_TECHNICIAN", description="System role if user account created")
    create_login_account: bool = Field(False, description="Whether to enable login credentials")
    password: Optional[str] = Field(None, min_length=8, description="Initial login password if creating login account")


class EmployeeUpdate(BaseModel):
    department_id: Optional[int] = None
    designation: Optional[str] = Field(None, min_length=2, max_length=100)
    employment_type: Optional[str] = None
    joining_date: Optional[date] = None
    exit_date: Optional[date] = None
    emergency_contact: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Linked user fields
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class EmployeeStatusUpdate(BaseModel):
    is_active: bool
    exit_date: Optional[date] = None


class EmployeeResponse(BaseModel):
    id: int
    employee_code: str
    designation: str
    employment_type: str
    joining_date: date
    exit_date: Optional[date] = None
    emergency_contact: Optional[str] = None
    is_active: bool
    
    # Department info
    department_id: int
    department_name: Optional[str] = None
    department_code: Optional[str] = None
    
    # Linked user info
    user_id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    user_role: Optional[str] = None
    user_is_active: bool = True
    has_login_access: bool = True
    
    # Skills and certifications
    skills: List[EmployeeSkillResponse] = []
    certifications: List[CertificationResponse] = []
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmployeeListResponse(BaseModel):
    items: List[EmployeeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
