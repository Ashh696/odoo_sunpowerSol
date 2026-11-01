from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from decimal import Decimal

VALID_WARRANTY_STATUSES = {
    "PENDING_ACTIVATION",
    "ACTIVE",
    "EXPIRED",
    "VOID",
    "CLAIMED",
}

VALID_WARRANTY_EVENT_TYPES = {
    "ACTIVATION",
    "CLAIM_RAISED",
    "INSPECTION",
    "REPAIR",
    "REPLACEMENT",
    "VOIDED",
}

VALID_TICKET_CATEGORIES = {
    "INVERTER_FAULT",
    "LOW_GENERATION",
    "PHYSICAL_DAMAGE",
    "GRID_FAILURE",
    "WIRING_ISSUE",
    "GENERAL",
}

VALID_TICKET_PRIORITIES = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
}

VALID_TICKET_STATUSES = {
    "OPEN",
    "ASSIGNED",
    "IN_PROGRESS",
    "RESOLVED",
    "CLOSED",
    "CANCELLED",
}

VALID_VISIT_STATUSES = {
    "SCHEDULED",
    "IN_PROGRESS",
    "COMPLETED",
    "RESCHEDULED",
}


# ==========================================
# 1. WARRANTY POLICIES
# ==========================================

class WarrantyPolicyCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    policy_code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=150)
    product_id: Optional[int] = None
    warranty_period_months: int = Field(..., gt=0)
    activation_trigger: str = Field(default="COMMISSIONING", max_length=50)
    terms_and_conditions: Optional[str] = None
    is_active: bool = True


class WarrantyPolicyResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    policy_code: str
    name: str
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    warranty_period_months: int
    activation_trigger: str
    terms_and_conditions: Optional[str] = None
    is_active: bool
    created_at: datetime


# ==========================================
# 2. WARRANTY RECORDS & EVENTS
# ==========================================

class WarrantyEventCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    event_type: str = Field(..., max_length=50)
    description: str = Field(..., min_length=3)


class WarrantyEventResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    warranty_record_id: int
    event_type: str
    event_date: datetime
    description: str
    recorded_by: int
    recorder_name: Optional[str] = None
    created_at: datetime


class WarrantyRecordCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    project_id: int = Field(..., gt=0)
    product_id: int = Field(..., gt=0)
    serial_number_id: int = Field(..., gt=0)
    warranty_policy_id: int = Field(..., gt=0)
    delivery_date: Optional[date] = None
    activation_date: Optional[date] = None
    warranty_start_date: Optional[date] = None


class ProjectWarrantyBatchRegister(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    activation_date: Optional[date] = None


class WarrantyRecordResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    certificate_number: str
    project_id: int
    project_code: Optional[str] = None
    product_id: int
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    serial_number_id: int
    serial_number: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    warranty_policy_id: int
    policy_name: Optional[str] = None
    warranty_period_months: Optional[int] = None
    delivery_date: date
    activation_trigger: str
    activation_date: Optional[date] = None
    warranty_start_date: date
    warranty_end_date: date
    status: str
    created_at: datetime


class WarrantyRecordDetailResponse(WarrantyRecordResponse):
    events: List[WarrantyEventResponse] = []


# ==========================================
# 3. SERVICE TICKETS
# ==========================================

class ServiceTicketCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    project_id: int = Field(..., gt=0)
    serial_number_id: Optional[int] = None
    warranty_record_id: Optional[int] = None
    issue_category: str = Field(default="GENERAL", max_length=50)
    priority: str = Field(default="MEDIUM", max_length=50)
    description: str = Field(..., min_length=5)


class ServiceTicketStatusUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    status: str = Field(..., max_length=50)
    notes: Optional[str] = None


class ServiceTicketResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    ticket_number: str
    project_id: int
    project_code: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    serial_number_id: Optional[int] = None
    serial_number: Optional[str] = None
    warranty_record_id: Optional[int] = None
    certificate_number: Optional[str] = None
    issue_category: str
    priority: str
    description: str
    status: str
    created_by: int
    creator_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ==========================================
# 4. SERVICE VISITS
# ==========================================

class ServiceVisitCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    technician_id: int = Field(..., gt=0)
    scheduled_date: date = Field(default_factory=date.today)
    notes: Optional[str] = None


class ServiceVisitComplete(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    findings: str = Field(..., min_length=3)
    action_taken: str = Field(..., min_length=3)
    parts_replaced: bool = False
    customer_present_name: Optional[str] = None


class ServiceVisitResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    ticket_id: int
    technician_id: int
    technician_name: Optional[str] = None
    visit_number: int
    scheduled_date: date
    visit_status: str
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    findings: Optional[str] = None
    action_taken: Optional[str] = None
    parts_replaced: bool
    customer_present_name: Optional[str] = None
    created_at: datetime


# ==========================================
# 5. COMPONENT REPLACEMENTS
# ==========================================

class ComponentReplacementCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    original_serial_id: int = Field(..., gt=0)
    replacement_serial_id: int = Field(..., gt=0)
    replacement_reason: str = Field(..., min_length=5)
    replacement_date: date = Field(default_factory=date.today)


class ReplacementResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    ticket_id: int
    original_serial_id: int
    original_serial_number: Optional[str] = None
    replacement_serial_id: int
    replacement_serial_number: Optional[str] = None
    replacement_reason: str
    replacement_date: date
    replaced_by: int
    replacer_name: Optional[str] = None
    created_at: datetime


# ==========================================
# 6. SERVICE TICKET CONFIRMATIONS
# ==========================================

class ServiceTicketConfirmationCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    resolution_confirmed: bool = True
    customer_rating: Optional[int] = Field(None, ge=1, le=5)
    customer_feedback: Optional[str] = None
    confirmation_channel: str = Field(default="PORTAL", max_length=50)


class ServiceTicketConfirmationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    ticket_id: int
    customer_id: int
    resolution_confirmed: bool
    customer_rating: Optional[int] = None
    customer_feedback: Optional[str] = None
    confirmed_at: datetime
    confirmation_channel: str
    created_at: datetime


# ==========================================
# 7. SERVICE TICKET DETAIL & SLA METRICS
# ==========================================

class ServiceTicketDetailResponse(ServiceTicketResponse):
    visits: List[ServiceVisitResponse] = []
    replacements: List[ReplacementResponse] = []
    confirmation: Optional[ServiceTicketConfirmationResponse] = None


class ServiceTicketSLAMetrics(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    total_open_tickets: int
    open_tickets_by_sla_aging: Dict[str, int]
    approaching_deadline_count: int
    overdue_response_count: int
    sla_compliance_percentage: float
    average_resolution_hours: Optional[float] = None
    resolution_trend: List[Dict[str, Any]] = []
