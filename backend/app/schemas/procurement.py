from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from decimal import Decimal

# ==========================================
# CONSTANTS & ALLOWED VALUES
# ==========================================

VALID_PO_STATUSES = {
    "DRAFT",
    "ISSUED",
    "PARTIALLY_RECEIVED",
    "RECEIVED",
    "CANCELLED",
}

VALID_GRN_STATUSES = {
    "ACCEPTED",
    "PARTIALLY_ACCEPTED",
    "REJECTED",
    "RECEIVED",
    "INSPECTED",
}

VALID_SERIAL_STATUSES = {
    "IN_STOCK",
    "RESERVED",
    "DISPATCHED",
    "INSTALLED",
    "COMMISSIONED",
    "IN_REPAIR",
    "REPLACED",
    "SCRAPPED",
}

VALID_STOCK_MOVEMENT_TYPES = {
    "PURCHASE_RECEIPT",
    "DISPATCH",
    "RETURN",
    "ADJUSTMENT",
    "SCRAP",
}


# ==========================================
# 1. SUPPLIER SCHEMAS
# ==========================================

class SupplierBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    company_name: str = Field(..., min_length=2, max_length=255, description="Registered legal/trade name")
    contact_person: str = Field(..., min_length=2, max_length=150, description="Primary contact person")
    email: str = Field(..., min_length=5, max_length=255, description="Primary contact email")
    phone: str = Field(..., min_length=7, max_length=30, description="Primary contact telephone")
    address: str = Field(..., min_length=3, description="Street address")
    city: str = Field(..., min_length=2, max_length=100, description="City")
    state: str = Field(..., min_length=2, max_length=100, description="State / Province")
    gst_number: Optional[str] = Field(None, max_length=30, description="15-character GSTIN or registration")
    pan_number: Optional[str] = Field(None, max_length=20, description="Permanent Account Number (PAN)")
    bank_account_details: Optional[str] = Field(None, description="Bank Name, A/C No, IFSC, Branch")


class SupplierCreate(SupplierBase):
    supplier_code: Optional[str] = Field(None, max_length=50, description="Unique vendor code, auto-generated if omitted")


class SupplierUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    company_name: Optional[str] = Field(None, min_length=2, max_length=255)
    contact_person: Optional[str] = Field(None, min_length=2, max_length=150)
    email: Optional[str] = Field(None, min_length=5, max_length=255)
    phone: Optional[str] = Field(None, min_length=7, max_length=30)
    address: Optional[str] = Field(None, min_length=3)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    gst_number: Optional[str] = Field(None, max_length=30)
    pan_number: Optional[str] = Field(None, max_length=20)
    bank_account_details: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierStatusUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    is_active: bool = Field(..., description="Active status toggle")


class SupplierResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    supplier_code: str
    company_name: str
    contact_person: str
    email: str
    phone: str
    address: str
    city: str
    state: str
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    bank_account_details: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SupplierListResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    supplier_code: str
    company_name: str
    contact_person: str
    email: str
    phone: str
    city: str
    state: str
    gst_number: Optional[str] = None
    is_active: bool
    created_at: datetime


# ==========================================
# 2. PURCHASE ORDER SCHEMAS
# ==========================================

class PurchaseOrderItemCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    product_id: int = Field(..., gt=0, description="Product catalog item ID")
    ordered_quantity: Decimal = Field(..., gt=0, description="Quantity ordered (> 0)")
    unit_price: Decimal = Field(..., ge=0, description="Per-unit procurement price (INR)")
    tax_rate_percent: Optional[Decimal] = Field(default=Decimal("12.00"), ge=0, description="Tax rate percentage (e.g. 12.00)")


class PurchaseOrderItemResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    purchase_order_id: int
    product_id: int
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    unit_of_measure: Optional[str] = None
    is_serialized: Optional[bool] = False
    ordered_quantity: Decimal
    received_quantity: Decimal
    unit_price: Decimal
    tax_rate_percent: Decimal
    total_amount: Decimal
    created_at: datetime


class PurchaseOrderCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    supplier_id: int = Field(..., gt=0, description="Active supplier ID")
    project_id: Optional[int] = Field(None, gt=0, description="Optional project ID for project-tied procurement")
    po_date: date = Field(default_factory=date.today, description="Order date")
    expected_delivery_date: Optional[date] = Field(None, description="Expected delivery date (>= po_date)")
    notes: Optional[str] = Field(None, max_length=1000, description="Order instructions or terms")
    items: List[PurchaseOrderItemCreate] = Field(..., min_length=1, description="Purchase order line items")


class PurchaseOrderUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    supplier_id: Optional[int] = Field(None, gt=0)
    project_id: Optional[int] = None
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=1000)
    items: Optional[List[PurchaseOrderItemCreate]] = Field(None, min_length=1)


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    po_number: str
    supplier_id: int
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None
    project_id: Optional[int] = None
    project_code: Optional[str] = None
    po_date: date
    expected_delivery_date: Optional[date] = None
    total_amount: Decimal
    tax_amount: Decimal
    status: str
    created_by: int
    creator_name: Optional[str] = None
    notes: Optional[str] = None
    items_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime


class PurchaseOrderDetailResponse(PurchaseOrderResponse):
    items: List[PurchaseOrderItemResponse] = []


# ==========================================
# 3. GOODS RECEIPT (GRN) SCHEMAS
# ==========================================

class GoodsReceiptItemCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    po_item_id: int = Field(..., gt=0, description="Purchase order line item ID")
    product_id: int = Field(..., gt=0, description="Product catalog item ID")
    received_quantity: Decimal = Field(..., ge=0, description="Total physical quantity delivered")
    accepted_quantity: Decimal = Field(..., ge=0, description="Quantity accepted into inventory")
    rejected_quantity: Decimal = Field(default=Decimal("0.00"), ge=0, description="Quantity rejected")
    rejection_reason: Optional[str] = Field(None, max_length=255, description="Reason if rejected_quantity > 0")
    serial_numbers: Optional[List[str]] = Field(default=[], description="Serial numbers for serialized products (must match accepted_quantity)")


class GoodsReceiptItemResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    goods_receipt_id: int
    po_item_id: int
    product_id: int
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    received_quantity: Decimal
    accepted_quantity: Decimal
    rejected_quantity: Decimal
    rejection_reason: Optional[str] = None
    created_at: datetime


class GoodsReceiptCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    purchase_order_id: int = Field(..., gt=0, description="Issued Purchase Order ID")
    received_date: date = Field(default_factory=date.today, description="Physical goods receipt date")
    challan_number: Optional[str] = Field(None, max_length=100, description="Supplier Delivery Challan / Invoice No")
    challan_date: Optional[date] = Field(None, description="Date on delivery challan")
    inspection_remarks: Optional[str] = Field(None, max_length=1000, description="Quality / QA remarks")
    items: List[GoodsReceiptItemCreate] = Field(..., min_length=1, description="Inspected items")


class GoodsReceiptResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    grn_number: str
    purchase_order_id: int
    po_number: Optional[str] = None
    supplier_id: int
    supplier_name: Optional[str] = None
    received_date: date
    received_by: int
    receiver_name: Optional[str] = None
    challan_number: Optional[str] = None
    challan_date: Optional[date] = None
    status: str
    inspection_remarks: Optional[str] = None
    items_count: Optional[int] = 0
    created_at: datetime


class GoodsReceiptDetailResponse(GoodsReceiptResponse):
    items: List[GoodsReceiptItemResponse] = []


# ==========================================
# 4. INVENTORY & STOCK LEDGER SCHEMAS
# ==========================================

class InventoryItemResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    product_id: int
    product_code: str
    product_name: str
    category: str
    brand: Optional[str] = None
    model_number: Optional[str] = None
    unit_of_measure: str
    is_serialized: bool
    warehouse_location: str
    quantity_on_hand: Decimal
    reserved_quantity: Decimal
    quantity_available: Decimal
    average_unit_cost: Decimal
    reorder_level: Decimal
    is_low_stock: bool
    total_valuation: Decimal
    last_restocked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class StockMovementResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    inventory_id: int
    product_id: int
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    movement_type: str
    reference_type: str
    reference_id: Optional[int] = None
    quantity: Decimal
    unit_cost: Decimal
    quantity_before: Decimal
    quantity_after: Decimal
    performed_by: int
    performer_name: Optional[str] = None
    remarks: Optional[str] = None
    created_at: datetime


class SerialNumberResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    serial_number: str
    product_id: int
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    inventory_id: Optional[int] = None
    purchase_order_id: Optional[int] = None
    po_number: Optional[str] = None
    project_id: Optional[int] = None
    project_code: Optional[str] = None
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    status: str
    warranty_months: int
    received_date: date
    created_at: datetime
    updated_at: datetime


# ==========================================
# 5. PROJECT MATERIAL SHORTAGE SCHEMAS
# ==========================================

class ProjectMaterialShortageItem(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    bom_item_id: int
    product_id: int
    product_code: str
    product_name: str
    category: str
    unit_of_measure: str
    planned_quantity: Decimal
    allocated_quantity: Decimal
    unallocated_quantity: Decimal
    quantity_on_hand: Decimal
    quantity_available: Decimal
    shortage_quantity: Decimal
    has_shortage: bool


class ProjectMaterialShortageResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    project_id: int
    project_code: str
    system_capacity_kw: Decimal
    system_type: str
    total_bom_items: int
    shortage_items_count: int
    items: List[ProjectMaterialShortageItem]
