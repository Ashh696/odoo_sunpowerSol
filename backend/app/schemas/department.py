from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, description="Department name")
    code: str = Field(..., min_length=2, max_length=50, description="Unique department code, e.g. TECH, SALES")
    manager_id: Optional[int] = Field(None, description="User ID of department manager (references users.id)")
    is_active: bool = Field(True, description="Whether department is operational")


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    manager_id: Optional[int] = None
    is_active: Optional[bool] = None


class DepartmentResponse(BaseModel):
    id: int
    name: str
    code: str
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    manager_email: Optional[str] = None
    is_active: bool
    employee_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DepartmentDetailResponse(DepartmentResponse):
    pass
