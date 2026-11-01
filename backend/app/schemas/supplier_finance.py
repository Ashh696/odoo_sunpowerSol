from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from decimal import Decimal

VALID_SUPPLIER_INVOICE_STATUSES = {
    "PENDING",
    "PARTIALLY_PAID",
    "PAID",
    "OVERDUE",
    "DISPUTED",
    "CANCELLED",
}

VALID_PAYMENT_MODES = {
    "NEFT",
    "RTGS",
    "IMPS",
    "UPI",
    "CHEQUE",
    "BANK_TRANSFER",
    "CASH",
}

VALID_COST_CATEGORIES = {
    "MATERIAL",
    "LABOR",
    "TRANSPORT",
    "PERMITS_DISCOM",
    "CIVIL_WORK",
    "EQUIPMENT_RENTAL",
    "MISCELLANEOUS",
}


# ==========================================
# 1. SUPPLIER INVOICES (AP)
# ==========================================

class SupplierInvoiceCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    purchase_order_id: int = Field(..., gt=0)
    invoice_number: str = Field(..., min_length=2, max_length=100)
    invoice_date: date = Field(default_factory=date.today)
    due_date: Optional[date] = None
    subtotal: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(..., gt=0)


class SupplierInvoiceStatusUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    payment_status: str = Field(..., description="Target status: UNPAID, APPROVED, DISPUTED, CANCELLED")


class SupplierInvoicePaymentAllocationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    supplier_payment_id: int
    supplier_invoice_id: int
    payment_reference: Optional[str] = None
    allocated_amount: Decimal
    allocated_at: datetime


class SupplierInvoiceResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    invoice_number: str
    purchase_order_id: int
    po_number: Optional[str] = None
    po_total: Optional[Decimal] = None
    supplier_id: int
    supplier_name: Optional[str] = None
    supplier_gstin: Optional[str] = None
    invoice_date: date
    due_date: Optional[date] = None
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    balance_amount: Decimal
    payment_status: str
    variance_amount: Optional[Decimal] = Decimal("0.00")
    created_at: datetime
    updated_at: datetime


class SupplierInvoiceDetailResponse(SupplierInvoiceResponse):
    allocations: List[SupplierInvoicePaymentAllocationResponse] = []


# ==========================================
# 2. SUPPLIER PAYMENTS
# ==========================================

class SupplierPaymentCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    supplier_id: int = Field(..., gt=0)
    payment_reference: Optional[str] = Field(None, max_length=100)
    payment_date: date = Field(default_factory=date.today)
    payment_mode: str = Field(default="BANK_TRANSFER")
    amount: Decimal = Field(..., gt=0)
    notes: Optional[str] = Field(None, max_length=1000)


class SupplierPaymentAllocationCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    supplier_payment_id: int = Field(..., gt=0)
    allocated_amount: Decimal = Field(..., gt=0)


class DirectSupplierInvoicePaymentCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    amount: Decimal = Field(..., gt=0)
    payment_mode: str = Field(default="BANK_TRANSFER")
    payment_reference: Optional[str] = Field(None, max_length=100)
    payment_date: date = Field(default_factory=date.today)
    notes: Optional[str] = Field(None, max_length=1000)


class SupplierPaymentResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    payment_reference: str
    supplier_id: int
    supplier_name: Optional[str] = None
    payment_date: date
    payment_mode: str
    amount: Decimal
    unallocated_amount: Decimal
    status: str
    notes: Optional[str] = None
    created_by: int
    creator_name: Optional[str] = None
    created_at: datetime


# ==========================================
# 3. PROJECT COSTS & PROFITABILITY
# ==========================================

class ProjectCostCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    cost_category: str = Field(..., max_length=50)
    cost_amount: Decimal = Field(..., gt=0)
    source_reference_type: Optional[str] = Field(None, max_length=50)
    source_reference_id: Optional[int] = None


class ProjectCostResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    project_id: int
    cost_category: str
    cost_amount: Decimal
    source_reference_type: Optional[str] = None
    source_reference_id: Optional[int] = None
    recorded_by: int
    recorder_name: Optional[str] = None
    created_at: datetime


class ProjectProfitabilityResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    project_id: int
    project_code: str
    order_id: int
    order_number: str
    customer_name: str
    contract_amount: Decimal
    total_invoiced: Decimal
    total_collected: Decimal
    material_cost: Decimal
    labor_installation_cost: Decimal
    other_direct_costs: Decimal
    total_incurred_cost: Decimal
    gross_profit: Decimal
    gross_margin_percentage: Decimal
