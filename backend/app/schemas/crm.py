from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from decimal import Decimal


# ==========================================
# CUSTOMER SCHEMAS
# ==========================================

class CustomerBase(BaseModel):
    customer_type: str = Field(default="RESIDENTIAL", description="RESIDENTIAL, COMMERCIAL, INDUSTRIAL")
    full_name: str = Field(..., min_length=2, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: str = Field(..., min_length=7, max_length=30)
    alternate_phone: Optional[str] = Field(None, max_length=30)
    address: str = Field(..., min_length=3)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    pincode: str = Field(..., min_length=3, max_length=20)
    electricity_consumer_number: Optional[str] = Field(None, max_length=100)
    sanctioned_load_kw: Optional[float] = Field(None, ge=0)

    @field_validator("customer_type")
    @classmethod
    def validate_customer_type(cls, v: str) -> str:
        allowed = {"RESIDENTIAL", "COMMERCIAL", "INDUSTRIAL", "INDIVIDUAL"}
        clean = v.strip().upper()
        if clean not in allowed:
            raise ValueError(f"customer_type must be one of {allowed}")
        if clean == "INDIVIDUAL":
            return "RESIDENTIAL"
        return clean


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    customer_type: Optional[str] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, min_length=7, max_length=30)
    alternate_phone: Optional[str] = None
    address: Optional[str] = Field(None, min_length=3)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    pincode: Optional[str] = Field(None, min_length=3, max_length=20)
    electricity_consumer_number: Optional[str] = None
    sanctioned_load_kw: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None

    @field_validator("customer_type")
    @classmethod
    def validate_customer_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"RESIDENTIAL", "COMMERCIAL", "INDUSTRIAL", "INDIVIDUAL"}
            clean = v.strip().upper()
            if clean not in allowed:
                raise ValueError(f"customer_type must be one of {allowed}")
            if clean == "INDIVIDUAL":
                return "RESIDENTIAL"
            return clean
        return v


class CustomerResponse(CustomerBase):
    id: int
    user_id: Optional[int] = None
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    is_active: bool
    enquiry_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    items: List[CustomerResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# ==========================================
# ENQUIRY SCHEMAS
# ==========================================

VALID_ENQUIRY_SOURCES = {"DIRECT", "WEBSITE", "REFERRAL", "CAMPAIGN", "WHATSAPP", "PHONE"}
VALID_SYSTEM_TYPES = {"ON_GRID", "OFF_GRID", "HYBRID"}
VALID_ENQUIRY_STATUSES = {
    "NEW",
    "CONTACTED",
    "SURVEY_REQUESTED",
    "QUOTED",
    "WON",
    "LOST",
    "CANCELLED",
}
VALID_ROOF_TYPES = {"RCC_FLAT", "METAL_SHED", "TILED_ROOF", "OTHER"}


class EnquiryBase(BaseModel):
    customer_id: int
    source: str = Field(default="DIRECT")
    system_type: str = Field(default="ON_GRID")
    proposed_capacity_kw: float = Field(default=3.0, gt=0, le=500.0)
    monthly_electricity_bill: Optional[float] = Field(None, ge=0)
    roof_type: Optional[str] = Field(default="RCC_FLAT")
    assigned_sales_id: Optional[int] = None
    notes: Optional[str] = None

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        clean = v.strip().upper()
        if clean not in VALID_ENQUIRY_SOURCES:
            return clean
        return clean

    @field_validator("system_type")
    @classmethod
    def validate_system_type(cls, v: str) -> str:
        clean = v.strip().upper()
        if clean not in VALID_SYSTEM_TYPES:
            raise ValueError(f"system_type must be one of {VALID_SYSTEM_TYPES}")
        return clean

    @field_validator("roof_type")
    @classmethod
    def validate_roof_type(cls, v: Optional[str]) -> Optional[str]:
        if v:
            clean = v.strip().upper()
            return clean
        return v


class EnquiryCreate(EnquiryBase):
    pass


class EnquiryUpdate(BaseModel):
    source: Optional[str] = None
    system_type: Optional[str] = None
    proposed_capacity_kw: Optional[float] = Field(None, gt=0, le=500.0)
    monthly_electricity_bill: Optional[float] = Field(None, ge=0)
    roof_type: Optional[str] = None
    assigned_sales_id: Optional[int] = None
    notes: Optional[str] = None

    @field_validator("system_type")
    @classmethod
    def validate_system_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().upper()
            if clean not in VALID_SYSTEM_TYPES:
                raise ValueError(f"system_type must be one of {VALID_SYSTEM_TYPES}")
            return clean
        return v


class EnquiryStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        clean = v.strip().upper()
        if clean not in VALID_ENQUIRY_STATUSES:
            raise ValueError(f"status must be one of {VALID_ENQUIRY_STATUSES}")
        return clean


class EnquiryAssignUpdate(BaseModel):
    assigned_sales_id: Optional[int] = None


class EnquiryResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_city: Optional[str] = None
    enquiry_number: str
    source: str
    system_type: str
    proposed_capacity_kw: float
    monthly_electricity_bill: Optional[float] = None
    roof_type: Optional[str] = None
    status: str
    assigned_sales_id: Optional[int] = None
    assigned_sales_name: Optional[str] = None
    assigned_sales_code: Optional[str] = None
    notes: Optional[str] = None
    followup_count: int = 0
    latest_followup_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EnquiryListResponse(BaseModel):
    items: List[EnquiryResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# ==========================================
# FOLLOWUP SCHEMAS
# ==========================================

VALID_FOLLOWUP_TYPES = {"CALL", "EMAIL", "VISIT", "WHATSAPP"}
VALID_FOLLOWUP_STATUSES = {"SCHEDULED", "COMPLETED", "CANCELLED"}


class FollowupBase(BaseModel):
    enquiry_id: int
    followup_type: str = Field(default="CALL")
    scheduled_at: datetime
    discussion_summary: Optional[str] = None
    next_followup_at: Optional[datetime] = None

    @field_validator("followup_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        clean = v.strip().upper()
        if clean not in VALID_FOLLOWUP_TYPES:
            raise ValueError(f"followup_type must be one of {VALID_FOLLOWUP_TYPES}")
        return clean


class FollowupCreate(FollowupBase):
    conducted_by: Optional[int] = None  # Optional; if None, derived from current authenticated employee


class FollowupComplete(BaseModel):
    discussion_summary: str = Field(..., min_length=2)
    completed_at: Optional[datetime] = None
    status: str = Field(default="COMPLETED")
    next_followup_at: Optional[datetime] = None
    update_enquiry_status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        clean = v.strip().upper()
        if clean not in VALID_FOLLOWUP_STATUSES:
            raise ValueError(f"status must be one of {VALID_FOLLOWUP_STATUSES}")
        return clean

    @field_validator("update_enquiry_status")
    @classmethod
    def validate_enquiry_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().upper()
            if clean not in VALID_ENQUIRY_STATUSES:
                raise ValueError(f"update_enquiry_status must be one of {VALID_ENQUIRY_STATUSES}")
            return clean
        return v


class FollowupReschedule(BaseModel):
    scheduled_at: datetime
    reason: str = Field(..., min_length=2, max_length=1000)


class FollowupResponse(BaseModel):
    id: int
    enquiry_id: int
    enquiry_number: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    conducted_by: int
    conductor_name: Optional[str] = None
    followup_type: str
    scheduled_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    discussion_summary: Optional[str] = None
    next_followup_at: Optional[datetime] = None
    is_overdue: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class FollowupListResponse(BaseModel):
    items: List[FollowupResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# ==========================================
# CRM DASHBOARD METRICS SCHEMA
# ==========================================

class CRMDashboardMetrics(BaseModel):
    total_customers: int
    active_customers: int
    total_enquiries: int
    enquiries_by_status: Dict[str, int]
    enquiries_by_source: Dict[str, int]
    enquiries_by_system_type: Dict[str, int]
    overdue_followups_count: int
    scheduled_today_followups_count: int
    conversion_rate_percentage: float = 0.0
    recent_enquiries: List[EnquiryResponse]
    pending_followups: List[FollowupResponse]
