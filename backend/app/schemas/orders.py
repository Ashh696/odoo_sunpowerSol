from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from decimal import Decimal

VALID_ORDER_STATUSES = {
    "PENDING_ADVANCE",
    "CONFIRMED",
    "PROCESSING",
    "COMPLETED",
    "CANCELLED",
}

VALID_PAYMENT_METHODS = {"NEFT", "RTGS", "CHEQUE", "UPI", "CASH"}


# ==========================================
# ORDER REQUEST SCHEMAS
# ==========================================

class OrderCreateRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    quotation_id: int = Field(..., description="ID of the accepted quotation to convert")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional creation notes")


class OrderStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    status: str = Field(..., description="Target status (CONFIRMED, PROCESSING, COMPLETED, CANCELLED)")
    notes: Optional[str] = Field(None, max_length=1000, description="Reason or notes for status update")


class OrderPaymentRecordRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    amount: Decimal = Field(..., gt=0, description="Payment amount received (> 0)")
    payment_method: str = Field(default="UPI", description="NEFT, RTGS, CHEQUE, UPI, CASH")
    transaction_reference: Optional[str] = Field(None, max_length=100, description="Unique bank/gateway transaction reference")
    notes: Optional[str] = Field(None, max_length=1000, description="Payment remarks")


# ==========================================
# SUMMARY / EMBEDDED SCHEMAS
# ==========================================

class OrderCustomerSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    full_name: str
    phone: str
    email: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class OrderQuotationSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    quotation_number: str
    system_type: str
    capacity_kw: Decimal
    gross_amount: Decimal
    net_payable_amount: Decimal
    status: str


class OrderProjectSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    project_code: str
    status: str
    system_capacity_kw: Decimal
    system_type: str
    planned_start_date: Optional[date] = None
    planned_completion_date: Optional[date] = None


class OrderPaymentSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    payment_number: str
    payment_date: date
    payment_method: str
    transaction_reference: Optional[str] = None
    amount: Decimal
    unallocated_amount: Decimal
    status: str
    notes: Optional[str] = None
    created_at: datetime


# ==========================================
# ORDER RESPONSE SCHEMAS
# ==========================================

class OrderResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    order_number: str
    quotation_id: int
    customer_id: int
    order_date: date
    total_amount: Decimal
    advance_paid: Decimal
    balance_amount: Decimal
    status: str
    created_by: int
    created_at: datetime
    updated_at: datetime

    # Associated nested details
    customer: Optional[OrderCustomerSummary] = None
    quotation: Optional[OrderQuotationSummary] = None
    project: Optional[OrderProjectSummary] = None
    payments: List[OrderPaymentSummary] = Field(default_factory=list)


class OrderListResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    items: List[OrderResponse]
    total: int
    page: int
    limit: int
    pages: int
