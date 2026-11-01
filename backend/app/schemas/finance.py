from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from decimal import Decimal
from datetime import date, datetime

VALID_INVOICE_TYPES = {
    "ADVANCE",
    "MILESTONE_DISPATCH",
    "MILESTONE_INSTALLATION",
    "FINAL",
    "SUBSIDY",
}

VALID_INVOICE_STATUSES = {
    "PENDING",
    "PARTIALLY_PAID",
    "PAID",
    "OVERDUE",
}

VALID_PAYMENT_METHODS = {"NEFT", "RTGS", "CHEQUE", "UPI", "CASH"}


# ==========================================
# INVOICE ITEM SCHEMAS
# ==========================================

class InvoiceItemCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    product_id: int = Field(..., description="ID of catalog product")
    item_description: Optional[str] = Field(None, max_length=255, description="Item description snapshot")
    quantity: Decimal = Field(..., gt=0, description="Quantity billed (must be > 0)")
    unit_price: Decimal = Field(..., ge=0, description="Unit price before tax")
    tax_rate_percent: Decimal = Field(default=Decimal("12.00"), ge=0, description="Applicable GST tax rate percentage")


class InvoiceItemResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    invoice_id: int
    product_id: int
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    item_description: str
    quantity: Decimal
    unit_price: Decimal
    tax_rate_percent: Decimal
    total_amount: Decimal
    created_at: datetime


# ==========================================
# PAYMENT ALLOCATION SCHEMAS
# ==========================================

class PaymentAllocationCreateRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    payment_id: int = Field(..., description="ID of existing payment receipt")
    allocated_amount: Decimal = Field(..., gt=0, description="Amount to allocate (must be > 0)")
    notes: Optional[str] = Field(None, max_length=500, description="Optional allocation remarks")


class PaymentAllocationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    payment_id: int
    payment_number: str
    invoice_id: int
    invoice_number: str
    allocated_amount: Decimal
    allocated_at: datetime
    created_at: datetime


# ==========================================
# INVOICE CREATE & UPDATE SCHEMAS
# ==========================================

class InvoiceCreateRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    order_id: int = Field(..., description="ID of customer order being billed")
    project_id: Optional[int] = Field(None, description="Optional ID of associated project")
    invoice_type: str = Field(..., description="ADVANCE, MILESTONE_DISPATCH, MILESTONE_INSTALLATION, FINAL, SUBSIDY")
    invoice_date: date = Field(default_factory=date.today, description="Billing date")
    due_date: date = Field(..., description="Payment due date (must be >= invoice_date)")
    items: List[InvoiceItemCreate] = Field(..., min_length=1, description="Line items for bill of supply / tax invoice")
    notes: Optional[str] = Field(None, max_length=1000, description="Commercial or banking notes")

    @field_validator("invoice_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        clean = v.strip().upper()
        if clean not in VALID_INVOICE_TYPES:
            raise ValueError(f"Invalid invoice_type '{clean}'. Permitted: {sorted(list(VALID_INVOICE_TYPES))}")
        return clean


class DirectInvoicePaymentRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    amount: Decimal = Field(..., gt=0, description="Payment amount (must be > 0 and <= invoice balance)")
    payment_method: str = Field(default="UPI", description="UPI, NEFT, RTGS, CHEQUE, CASH")
    transaction_reference: Optional[str] = Field(None, max_length=100, description="Bank/gateway reference")
    payment_date: Optional[date] = Field(default_factory=date.today, description="Receipt date")
    notes: Optional[str] = Field(None, max_length=1000, description="Payment remarks")

    @field_validator("payment_method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        clean = v.strip().upper()
        if clean not in VALID_PAYMENT_METHODS:
            raise ValueError(f"Invalid payment_method '{clean}'. Permitted: {sorted(list(VALID_PAYMENT_METHODS))}")
        return clean


# ==========================================
# INVOICE SUMMARY & RESPONSE SCHEMAS
# ==========================================

class InvoiceCustomerSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    full_name: str
    phone: str
    email: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    address: Optional[str] = None


class InvoiceOrderSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    order_number: str
    order_date: date
    total_amount: Decimal
    advance_paid: Decimal
    balance_amount: Decimal
    status: str


class InvoiceProjectSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    project_code: str
    status: str
    system_capacity_kw: Decimal
    system_type: str


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    invoice_number: str
    order_id: int
    project_id: Optional[int] = None
    customer_id: int
    invoice_type: str
    invoice_date: date
    due_date: date
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    balance_amount: Decimal
    payment_status: str
    created_at: datetime
    updated_at: datetime
    customer: Optional[InvoiceCustomerSummary] = None
    order: Optional[InvoiceOrderSummary] = None
    project: Optional[InvoiceProjectSummary] = None
    items: List[InvoiceItemResponse] = []
    allocations: List[PaymentAllocationResponse] = []


class InvoiceListResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    items: List[InvoiceResponse]
    total: int
    page: int
    limit: int
    pages: int
    total_billed: Optional[Decimal] = None
    total_paid: Optional[Decimal] = None
    total_outstanding: Optional[Decimal] = None


# ==========================================
# PAYMENT REGISTER RESPONSE SCHEMAS
# ==========================================

class PaymentAllocationSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    invoice_id: int
    invoice_number: str
    allocated_amount: Decimal
    allocated_at: datetime


class PaymentRegisterItemResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: int
    payment_number: str
    customer_id: int
    customer_name: Optional[str] = None
    order_id: int
    order_number: Optional[str] = None
    project_id: Optional[int] = None
    project_code: Optional[str] = None
    payment_date: date
    payment_method: str
    transaction_reference: Optional[str] = None
    amount: Decimal
    unallocated_amount: Decimal
    status: str
    notes: Optional[str] = None
    received_by: int
    receiver_name: Optional[str] = None
    created_at: datetime
    allocations: List[PaymentAllocationSummary] = []


class PaymentRegisterListResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    items: List[PaymentRegisterItemResponse]
    total: int
    page: int
    limit: int
    pages: int
    total_collected: Optional[Decimal] = None
    total_unallocated: Optional[Decimal] = None
