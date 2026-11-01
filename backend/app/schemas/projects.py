from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from decimal import Decimal
from app.schemas.orders import OrderCustomerSummary, OrderResponse
from app.schemas.bom import ProjectBomItemResponse

VALID_PROJECT_STATUSES = {
    "INITIATED",
    "PROCUREMENT",
    "DISPATCHED",
    "INSTALLATION",
    "COMMISSIONED",
    "HANDED_OVER",
    "ON_HOLD",
    "CANCELLED",
}

VALID_NOTE_TYPES = {
    "GENERAL",
    "SITE_ISSUE",
    "CUSTOMER_REQUEST",
    "SAFETY",
    "TECHNICAL",
}


# ==========================================
# PROJECT REQUEST SCHEMAS
# ==========================================

class ProjectHandoverRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    project_manager_id: Optional[int] = Field(None, description="Employee ID of the assigned Project Manager")
    site_address: Optional[str] = Field(None, description="Installation site address (falls back to quotation/customer address if omitted)")
    planned_start_date: Optional[date] = Field(None, description="Planned installation start date (defaults to today)")
    planned_completion_date: Optional[date] = Field(None, description="Planned completion date (defaults to start date + 30 days)")
    initial_notes: Optional[str] = Field(None, max_length=2000, description="Initial technical handover notes")


class ProjectUpdateRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    project_manager_id: Optional[int] = Field(None, description="Update assigned Project Manager")
    planned_start_date: Optional[date] = None
    planned_completion_date: Optional[date] = None
    actual_completion_date: Optional[date] = None
    status: Optional[str] = Field(None, description="Target project execution status")
    site_address: Optional[str] = None


class ProjectNoteCreateRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    note_type: str = Field(default="GENERAL", description="GENERAL, SITE_ISSUE, CUSTOMER_REQUEST, SAFETY, TECHNICAL")
    content: str = Field(..., min_length=1, max_length=3000, description="Note content")
    is_internal: bool = Field(default=True, description="Whether the note is internal to company staff")


# ==========================================
# PROJECT DETAIL SCHEMAS
# ==========================================

class ProjectNoteResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    project_id: int
    note_type: str
    content: str
    is_internal: bool
    author_id: int
    author_name: Optional[str] = None
    created_at: datetime


class ProjectTaskResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    task_code: str
    title: str
    task_type: str
    priority: str
    status: str
    due_date: Optional[date] = None
    created_at: datetime


class ProjectResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    project_code: str
    order_id: int
    customer_id: int
    project_manager_id: Optional[int] = None
    project_manager_name: Optional[str] = None
    system_capacity_kw: Decimal
    system_type: str
    site_address: str
    planned_start_date: date
    planned_completion_date: date
    actual_completion_date: Optional[date] = None
    status: str
    created_at: datetime
    updated_at: datetime

    # Associated nested records
    customer: Optional[OrderCustomerSummary] = None
    order: Optional[OrderResponse] = None
    bom_items: List[ProjectBomItemResponse] = Field(default_factory=list)
    notes: List[ProjectNoteResponse] = Field(default_factory=list)
    tasks: List[ProjectTaskResponse] = Field(default_factory=list)


class ProjectListResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    items: List[ProjectResponse]
    total: int
    page: int
    limit: int
    pages: int
