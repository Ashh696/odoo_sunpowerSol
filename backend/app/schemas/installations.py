from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from decimal import Decimal

VALID_SCHEDULE_STATUSES = {
    "SCHEDULED",
    "IN_PROGRESS",
    "COMPLETED",
    "POSTPONED",
    "CANCELLED",
}

VALID_INSTALLATION_STATUSES = {
    "IN_PROGRESS",
    "PENDING_INSPECTION",
    "COMPLETED",
    "FAILED_INSPECTION",
    "COMMISSIONED",
}

VALID_CHECKLIST_CATEGORIES = {
    "CIVIL",
    "MECHANICAL",
    "ELECTRICAL",
    "SAFETY",
    "COMMISSIONING",
}

VALID_TEST_NAMES = {
    "VOC_TEST",
    "ISC_TEST",
    "INSULATION_RESISTANCE",
    "EARTHING_RESISTANCE",
    "GRID_SYNC",
    "INVERTER_EFFICIENCY",
}


# ==========================================
# 1. SCHEDULE SCHEMAS
# ==========================================

class ScheduleTechnicianCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    employee_id: int = Field(..., gt=0)
    role_in_team: str = Field(default="TECHNICIAN", max_length=50)


class ScheduleTechnicianResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    schedule_id: int
    employee_id: int
    employee_name: Optional[str] = None
    role_in_team: str
    assigned_at: datetime


class InstallationScheduleCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    project_id: int = Field(..., gt=0)
    scheduled_start_date: date
    scheduled_end_date: date
    notes: Optional[str] = Field(None, max_length=1000)
    technicians: List[ScheduleTechnicianCreate] = Field(default=[])


class InstallationScheduleStatusUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    status: str = Field(..., description="Target status: SCHEDULED, IN_PROGRESS, COMPLETED, POSTPONED, CANCELLED")
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    notes: Optional[str] = None


class InstallationScheduleResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    project_id: int
    project_code: Optional[str] = None
    customer_name: Optional[str] = None
    scheduled_start_date: date
    scheduled_end_date: date
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    status: str
    notes: Optional[str] = None
    created_by: int
    creator_name: Optional[str] = None
    technicians_count: Optional[int] = 0
    technicians: List[ScheduleTechnicianResponse] = []
    created_at: datetime
    updated_at: datetime


# ==========================================
# 2. CHECKLIST SCHEMAS
# ==========================================

class InstallationChecklistCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    checklist_item: str = Field(..., min_length=3, max_length=255)
    category: str = Field(default="ELECTRICAL", max_length=50)
    is_checked: bool = False
    remarks: Optional[str] = Field(None, max_length=500)


class InstallationChecklistUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    is_checked: bool
    remarks: Optional[str] = None


class InstallationChecklistResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    installation_id: int
    checklist_item: str
    category: str
    is_checked: bool
    remarks: Optional[str] = None
    verified_by: Optional[int] = None
    verifier_name: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime


# ==========================================
# 3. WORKLOG SCHEMAS
# ==========================================

class TechnicianWorklogCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    employee_id: int = Field(..., gt=0)
    work_date: date = Field(default_factory=date.today)
    hours_worked: Decimal = Field(..., gt=0, le=24)
    work_description: str = Field(..., min_length=5, max_length=1000)


class TechnicianWorklogResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    installation_id: int
    employee_id: int
    employee_name: Optional[str] = None
    work_date: date
    hours_worked: Decimal
    work_description: str
    approved_by: Optional[int] = None
    approver_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime


# ==========================================
# 4. ELECTRICAL TEST SCHEMAS
# ==========================================

class InstallationTestCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    test_name: str = Field(..., min_length=3, max_length=100)
    standard_value: Optional[str] = Field(None, max_length=100)
    measured_value: str = Field(..., min_length=1, max_length=100)
    unit_of_measure: str = Field(..., min_length=1, max_length=30)
    is_passed: bool = True
    tested_by: int = Field(..., gt=0)
    test_date: date = Field(default_factory=date.today)
    remarks: Optional[str] = Field(None, max_length=500)


class InstallationTestResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    installation_id: int
    test_name: str
    standard_value: Optional[str] = None
    measured_value: str
    unit_of_measure: str
    is_passed: bool
    tested_by: int
    tester_name: Optional[str] = None
    test_date: date
    remarks: Optional[str] = None
    created_at: datetime


# ==========================================
# 5. MATERIAL CONSUMPTION SCHEMAS
# ==========================================

class MaterialConsumptionCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    product_id: int = Field(..., gt=0)
    serial_number_id: Optional[int] = None
    quantity_consumed: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="NOS", max_length=50)
    is_extra_material: bool = False
    remarks: Optional[str] = Field(None, max_length=500)


class MaterialConsumptionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    installation_id: int
    product_id: int
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    serial_number_id: Optional[int] = None
    serial_number: Optional[str] = None
    quantity_consumed: Decimal
    unit_of_measure: str
    is_extra_material: bool
    remarks: Optional[str] = None
    created_at: datetime


# ==========================================
# 6. CUSTOMER ACCEPTANCE SCHEMAS
# ==========================================

class CustomerAcceptanceCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    acceptance_date: date = Field(default_factory=date.today)
    rating_overall: Optional[int] = Field(None, ge=1, le=5)
    satisfaction_notes: Optional[str] = Field(None, max_length=1000)
    acceptance_notes: Optional[str] = Field(None, max_length=1000)
    customer_name: Optional[str] = Field(None, max_length=255)
    customer_signature: Optional[str] = Field(None, max_length=255)
    is_accepted: bool = True


class CustomerAcceptanceResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    installation_id: int
    project_id: int
    customer_id: int
    customer_name: Optional[str] = None
    acceptance_date: date
    rating_overall: Optional[int] = None
    satisfaction_notes: Optional[str] = None
    is_accepted: bool
    created_at: datetime


# ==========================================
# 7. MAIN INSTALLATION SCHEMAS
# ==========================================

class InstallationCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    project_id: int = Field(..., gt=0)
    schedule_id: Optional[int] = None
    lead_technician_id: int = Field(..., gt=0)
    system_capacity_kw: Decimal = Field(..., gt=0)
    inverter_make_model: Optional[str] = Field(None, max_length=150)
    total_panels_installed: int = Field(..., ge=0)
    structure_type: Optional[str] = Field(None, max_length=100)
    installation_date: date = Field(default_factory=date.today)
    technician_notes: Optional[str] = Field(None, max_length=1000)


class InstallationStatusUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    status: str = Field(..., description="Target status: IN_PROGRESS, PENDING_INSPECTION, COMPLETED, FAILED_INSPECTION, COMMISSIONED")
    commissioning_date: Optional[date] = None
    technician_notes: Optional[str] = None


class InstallationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    project_id: int
    project_code: Optional[str] = None
    customer_name: Optional[str] = None
    site_address: Optional[str] = None
    schedule_id: Optional[int] = None
    lead_technician_id: int
    lead_technician_name: Optional[str] = None
    system_capacity_kw: Decimal
    inverter_make_model: Optional[str] = None
    total_panels_installed: int
    structure_type: Optional[str] = None
    installation_date: date
    commissioning_date: Optional[date] = None
    status: str
    technician_notes: Optional[str] = None
    is_commissioned: Optional[bool] = False
    created_at: datetime
    updated_at: datetime


class InstallationDetailResponse(InstallationResponse):
    checklists: List[InstallationChecklistResponse] = []
    tests: List[InstallationTestResponse] = []
    worklogs: List[TechnicianWorklogResponse] = []
    materials: List[MaterialConsumptionResponse] = []
    customer_acceptance: Optional[CustomerAcceptanceResponse] = None
