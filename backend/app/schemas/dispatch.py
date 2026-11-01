from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from decimal import Decimal

VALID_DISPATCH_STATUSES = {
    "PREPARED",
    "DISPATCHED",
    "IN_TRANSIT",
    "DELIVERED",
    "RETURNED",
}

VALID_CONFIRMATION_TYPES = {
    "CUSTOMER_SIGN",
    "OTP",
    "PHOTO",
    "SUPERVISOR_VERIFY",
}


# ==========================================
# 1. RESERVATION SCHEMAS
# ==========================================

class MaterialReservationCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    project_id: int = Field(..., gt=0)
    product_id: int = Field(..., gt=0)
    reserved_quantity: Decimal = Field(..., gt=0)
    expiry_date: Optional[date] = None


class MaterialReservationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    inventory_id: int
    product_id: int
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    project_id: int
    project_code: Optional[str] = None
    reserved_quantity: Decimal
    status: str
    reserved_by: int
    expiry_date: Optional[date] = None
    created_at: datetime


# ==========================================
# 2. DISPATCH SCHEMAS
# ==========================================

class DispatchSerialItem(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    serial_number_id: int
    serial_number: Optional[str] = None


class DispatchItemCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    product_id: int = Field(..., gt=0)
    dispatched_quantity: Decimal = Field(..., gt=0)
    serial_number_ids: Optional[List[int]] = Field(default=[])


class DispatchItemResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    dispatch_id: int
    product_id: int
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    unit_of_measure: Optional[str] = None
    is_serialized: Optional[bool] = False
    dispatched_quantity: Decimal
    serials: List[DispatchSerialItem] = []
    created_at: datetime


class DispatchCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    project_id: int = Field(..., gt=0)
    dispatched_date: date = Field(default_factory=date.today)
    vehicle_number: Optional[str] = Field(None, max_length=50)
    driver_name: Optional[str] = Field(None, max_length=150)
    driver_phone: Optional[str] = Field(None, max_length=30)
    tracking_number: Optional[str] = Field(None, max_length=100)
    remarks: Optional[str] = Field(None, max_length=1000)
    items: List[DispatchItemCreate] = Field(..., min_length=1)


class DispatchStatusUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    dispatch_status: str = Field(..., description="Target status: PREPARED, DISPATCHED, IN_TRANSIT, DELIVERED, RETURNED")
    remarks: Optional[str] = None


class DeliveryConfirmationCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    confirmation_type: str = Field(default="CUSTOMER_SIGN")
    recipient_name: str = Field(..., min_length=2, max_length=150)
    recipient_phone: str = Field(..., min_length=7, max_length=30)
    delivery_notes: Optional[str] = Field(None, max_length=1000)


class DeliveryConfirmationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    dispatch_id: int
    project_id: int
    confirmed_by: int
    confirmer_name: Optional[str] = None
    confirmation_type: str
    recipient_name: str
    recipient_phone: str
    confirmation_timestamp: datetime
    delivery_notes: Optional[str] = None
    created_at: datetime


class DispatchResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    dispatch_number: str
    project_id: int
    project_code: Optional[str] = None
    order_id: int
    order_number: Optional[str] = None
    customer_name: Optional[str] = None
    site_address: Optional[str] = None
    dispatched_date: date
    dispatch_status: str
    vehicle_number: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    tracking_number: Optional[str] = None
    dispatched_by: int
    dispatcher_name: Optional[str] = None
    remarks: Optional[str] = None
    items_count: Optional[int] = 0
    is_confirmed: Optional[bool] = False
    created_at: datetime
    updated_at: datetime


class DispatchDetailResponse(DispatchResponse):
    items: List[DispatchItemResponse] = []
    delivery_confirmation: Optional[DeliveryConfirmationResponse] = None


# ==========================================
# 3. PROJECT MATERIAL READINESS VIEW
# ==========================================

class ProjectMaterialReadinessItem(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    product_id: int
    product_code: str
    product_name: str
    category: str
    unit_of_measure: str
    is_serialized: bool
    planned_quantity: Decimal
    allocated_quantity: Decimal
    dispatched_quantity: Decimal
    installed_quantity: Decimal
    remaining_to_dispatch: Decimal
    warehouse_on_hand: Decimal
    warehouse_available: Decimal
    reserved_for_project: Decimal
    is_ready_for_dispatch: bool


class ProjectMaterialReadinessResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    project_id: int
    project_code: str
    order_id: int
    order_number: str
    customer_name: str
    site_address: str
    project_status: str
    all_ready_for_dispatch: bool
    items: List[ProjectMaterialReadinessItem]
