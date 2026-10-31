from typing import Optional
from pydantic import BaseModel, Field
from datetime import date, datetime


class CertificationCreate(BaseModel):
    certification_name: str = Field(..., min_length=2, max_length=255)
    issuing_authority: str = Field(..., min_length=2, max_length=255)
    certificate_number: Optional[str] = Field(None, max_length=100)
    issue_date: date
    expiry_date: Optional[date] = None
    attachment_id: Optional[int] = None
    verification_status: str = Field("PENDING", description="PENDING, VERIFIED, EXPIRED, REJECTED")


class CertificationUpdate(BaseModel):
    certification_name: Optional[str] = Field(None, min_length=2, max_length=255)
    issuing_authority: Optional[str] = Field(None, min_length=2, max_length=255)
    certificate_number: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    attachment_id: Optional[int] = None
    verification_status: Optional[str] = None


class CertificationResponse(BaseModel):
    id: int
    employee_id: int
    employee_code: Optional[str] = None
    employee_name: Optional[str] = None
    department_name: Optional[str] = None
    certification_name: str
    issuing_authority: str
    certificate_number: Optional[str] = None
    issue_date: date
    expiry_date: Optional[date] = None
    attachment_id: Optional[int] = None
    verification_status: str
    is_expired: bool = False
    days_to_expiry: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
