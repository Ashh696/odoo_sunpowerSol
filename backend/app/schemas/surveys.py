from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from decimal import Decimal

# Valid enum values from database check constraints and business rules
VALID_ROOF_ORIENTATIONS = {"SOUTH", "SOUTH_WEST", "SOUTH_EAST", "NORTH", "FLAT"}
VALID_ROOF_STRUCTURE_TYPES = {"ELEVATED", "FLUSH", "TIN_SHED"}
VALID_EXISTING_PHASES = {"SINGLE_PHASE", "THREE_PHASE"}
VALID_TECHNICAL_FEASIBILITIES = {"FEASIBLE", "NOT_FEASIBLE", "CONDITIONAL"}
VALID_SURVEY_STATUSES = {
    "DRAFT",
    "SUBMITTED",
    "UNDER_REVIEW",
    "APPROVED",
    "REJECTED",
    "CORRECTION_REQUESTED",
}
VALID_APPROVAL_ACTIONS = {"APPROVED", "REJECTED", "CORRECTION_REQUESTED"}


class SurveyBase(BaseModel):
    scheduled_at: datetime
    remarks: Optional[str] = None


class SurveyScheduleRequest(BaseModel):
    enquiry_id: int = Field(..., description="ID of the qualified enquiry to survey")
    surveyor_id: int = Field(..., description="Employee ID of the assigned surveyor")
    scheduled_at: datetime = Field(..., description="Target date and time for site visit")
    remarks: Optional[str] = Field(None, max_length=2000, description="Initial instructions or site notes")


class SurveyCreate(SurveyScheduleRequest):
    pass


class SurveyUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    conducted_at: Optional[datetime] = None
    roof_area_sqft: Optional[Decimal] = Field(None, ge=0, description="Total accessible roof area in sq ft")
    shadow_free_area_sqft: Optional[Decimal] = Field(None, ge=0, description="Shadow free usable roof area in sq ft")
    roof_orientation: Optional[str] = Field(None, description="SOUTH, SOUTH_WEST, SOUTH_EAST, NORTH, FLAT")
    roof_tilt_degrees: Optional[Decimal] = Field(None, ge=0, le=90, description="Roof pitch/tilt in degrees (0-90)")
    roof_structure_type: Optional[str] = Field(None, description="ELEVATED, FLUSH, TIN_SHED")
    existing_phase: Optional[str] = Field(None, description="SINGLE_PHASE, THREE_PHASE")
    sanctioned_load_kw: Optional[Decimal] = Field(None, ge=0, description="Sanctioned load from electricity meter in kW")
    gps_latitude: Optional[Decimal] = Field(None, ge=-90, le=90, description="GPS Latitude (-90 to +90)")
    gps_longitude: Optional[Decimal] = Field(None, ge=-180, le=180, description="GPS Longitude (-180 to +180)")
    technical_feasibility: Optional[str] = Field(None, description="FEASIBLE, NOT_FEASIBLE, CONDITIONAL")
    remarks: Optional[str] = Field(None, max_length=5000, description="Technical survey findings and surveyor notes")

    @field_validator("roof_orientation")
    @classmethod
    def validate_orientation(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().upper()
            if clean not in VALID_ROOF_ORIENTATIONS:
                raise ValueError(f"roof_orientation must be one of {VALID_ROOF_ORIENTATIONS}")
            return clean
        return v

    @field_validator("roof_structure_type")
    @classmethod
    def validate_structure(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().upper()
            if clean not in VALID_ROOF_STRUCTURE_TYPES:
                raise ValueError(f"roof_structure_type must be one of {VALID_ROOF_STRUCTURE_TYPES}")
            return clean
        return v

    @field_validator("existing_phase")
    @classmethod
    def validate_phase(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().upper()
            if clean not in VALID_EXISTING_PHASES:
                raise ValueError(f"existing_phase must be one of {VALID_EXISTING_PHASES}")
            return clean
        return v

    @field_validator("technical_feasibility")
    @classmethod
    def validate_feasibility(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().upper()
            if clean not in VALID_TECHNICAL_FEASIBILITIES:
                raise ValueError(f"technical_feasibility must be one of {VALID_TECHNICAL_FEASIBILITIES}")
            return clean
        return v


class SurveyApprovalCreate(BaseModel):
    action: str = Field(..., description="APPROVED, REJECTED, CORRECTION_REQUESTED")
    comments: str = Field(..., max_length=5000, description="Detailed technical review comments")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        clean = v.strip().upper()
        if clean not in VALID_APPROVAL_ACTIONS:
            raise ValueError(f"action must be one of {VALID_APPROVAL_ACTIONS}")
        return clean


class SurveyApprovalResponse(BaseModel):
    id: int
    survey_id: int
    reviewer_id: int
    reviewer_name: Optional[str] = None
    reviewer_role: Optional[str] = None
    action: str
    comments: str
    revision_number: int
    reviewed_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class FileAttachmentResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    file_name: str
    file_size_bytes: int
    mime_type: str
    storage_backend: str
    uploaded_by: int
    uploader_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SurveyResponse(BaseModel):
    id: int
    enquiry_id: int
    enquiry_number: Optional[str] = None
    proposed_capacity_kw: Optional[float] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_city: Optional[str] = None
    customer_address: Optional[str] = None
    surveyor_id: int
    surveyor_name: Optional[str] = None
    surveyor_code: Optional[str] = None
    survey_number: str
    scheduled_at: datetime
    conducted_at: Optional[datetime] = None
    roof_area_sqft: Optional[float] = None
    shadow_free_area_sqft: Optional[float] = None
    roof_orientation: Optional[str] = None
    roof_tilt_degrees: Optional[float] = None
    roof_structure_type: Optional[str] = None
    existing_phase: str
    sanctioned_load_kw: Optional[float] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    technical_feasibility: str
    remarks: Optional[str] = None
    status: str
    approval_count: int = 0
    latest_approval_action: Optional[str] = None
    latest_approval_comments: Optional[str] = None
    attachment_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SurveyDetailResponse(SurveyResponse):
    approvals: List[SurveyApprovalResponse] = []
    attachments: List[FileAttachmentResponse] = []


class SurveyListResponse(BaseModel):
    items: List[SurveyResponse]
    total: int
    page: int
    limit: int
    total_pages: int
