from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime, date
from decimal import Decimal

VALID_QUOTATION_STATUSES = {
    "DRAFT",
    "PENDING_APPROVAL",
    "APPROVED",
    "SENT",
    "ACCEPTED",
    "REJECTED",
    "REVISED",
    "EXPIRED",
}

VALID_SYSTEM_TYPES = {"ON_GRID", "OFF_GRID", "HYBRID"}


# ==========================================
# QUOTATION ITEM SCHEMAS
# ==========================================

class QuotationItemBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    product_id: int = Field(..., description="Active catalog product ID")
    item_description: Optional[str] = Field(None, max_length=255, description="Item description (defaults to product name)")
    quantity: Decimal = Field(..., gt=0, description="Quantity (> 0)")
    unit_price: Optional[Decimal] = Field(None, ge=0, description="Unit price (defaults to product base price)")
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Discount amount (non-negative, <= line base)")
    tax_rate_percent: Optional[Decimal] = Field(None, ge=0, le=100, description="Tax rate % (defaults to product tax rate)")


class QuotationItemCreate(QuotationItemBase):
    pass


class QuotationItemUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: Optional[int] = None
    product_id: Optional[int] = None
    item_description: Optional[str] = Field(None, max_length=255)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    tax_rate_percent: Optional[Decimal] = Field(None, ge=0, le=100)


class QuotationItemResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    quotation_id: int
    product_id: int
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    brand: Optional[str] = None
    model_number: Optional[str] = None
    item_description: str
    quantity: float
    unit_price: float
    discount_amount: float
    tax_rate_percent: float
    total_amount: float
    created_at: datetime


# ==========================================
# QUOTATION REVISION SCHEMAS
# ==========================================

class QuotationRevisionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    quotation_id: int
    revision_number: int
    snapshot_data: Dict[str, Any]
    reason_for_revision: str
    revised_by: int
    revised_by_name: Optional[str] = None
    created_at: datetime


class QuotationRevisionRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    reason_for_revision: str = Field(..., min_length=3, max_length=2000, description="Mandatory justification for revision")
    system_type: Optional[str] = Field(None, description="ON_GRID, OFF_GRID, HYBRID")
    capacity_kw: Optional[Decimal] = Field(None, gt=0)
    installation_cost: Optional[Decimal] = Field(None, ge=0)
    subsidy_estimate: Optional[Decimal] = Field(None, ge=0)
    subsidy_override_reason: Optional[str] = Field(None, max_length=1000)
    valid_until: Optional[date] = None
    terms_and_conditions: Optional[str] = None
    items: Optional[List[QuotationItemCreate]] = None

    @field_validator("system_type")
    @classmethod
    def validate_system_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.upper() not in VALID_SYSTEM_TYPES:
            raise ValueError(f"system_type must be one of {sorted(VALID_SYSTEM_TYPES)}")
        return v.upper() if v else None


# ==========================================
# QUOTATION CREATE & UPDATE SCHEMAS
# ==========================================

class QuotationCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    enquiry_id: int = Field(..., description="ID of associated enquiry")
    survey_id: Optional[int] = Field(None, description="ID of approved technical survey")
    system_type: Optional[str] = Field(None, description="ON_GRID, OFF_GRID, HYBRID (defaults to enquiry system type)")
    capacity_kw: Optional[Decimal] = Field(None, gt=0, description="Capacity in kW (defaults to enquiry proposed capacity)")
    installation_cost: Decimal = Field(default=Decimal("0.00"), ge=0, description="Installation and commissioning cost")
    subsidy_estimate: Optional[Decimal] = Field(None, ge=0, description="Estimated DBT subsidy (defaults to policy calculation)")
    subsidy_override_reason: Optional[str] = Field(None, max_length=1000, description="Required if subsidy estimate overrides standard policy")
    valid_until: Optional[date] = Field(None, description="Expiration date (defaults to quotation_date + 30 days)")
    terms_and_conditions: Optional[str] = Field(None, description="Standard or customized terms and conditions")
    items: List[QuotationItemCreate] = Field(..., min_length=1, description="List of quotation line items")

    @field_validator("system_type")
    @classmethod
    def validate_system_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.upper() not in VALID_SYSTEM_TYPES:
            raise ValueError(f"system_type must be one of {sorted(VALID_SYSTEM_TYPES)}")
        return v.upper() if v else None


class QuotationUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    system_type: Optional[str] = Field(None, description="ON_GRID, OFF_GRID, HYBRID")
    capacity_kw: Optional[Decimal] = Field(None, gt=0)
    installation_cost: Optional[Decimal] = Field(None, ge=0)
    subsidy_estimate: Optional[Decimal] = Field(None, ge=0)
    subsidy_override_reason: Optional[str] = Field(None, max_length=1000)
    valid_until: Optional[date] = None
    terms_and_conditions: Optional[str] = None
    items: Optional[List[QuotationItemCreate]] = None

    @field_validator("system_type")
    @classmethod
    def validate_system_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.upper() not in VALID_SYSTEM_TYPES:
            raise ValueError(f"system_type must be one of {sorted(VALID_SYSTEM_TYPES)}")
        return v.upper() if v else None


# ==========================================
# WORKFLOW ACTION SCHEMAS
# ==========================================

class QuotationApprovalRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    comments: Optional[str] = Field(None, max_length=1000, description="Optional review / approval notes")


class QuotationRejectionRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    comments: str = Field(..., min_length=3, max_length=1000, description="Mandatory reason for rejection")


class QuotationCustomerAcceptRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    acceptance_notes: Optional[str] = Field(None, max_length=1000, description="Optional customer acceptance notes")


class QuotationCustomerRejectRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    rejection_reason: str = Field(..., min_length=3, max_length=1000, description="Mandatory reason for declining quotation")


# ==========================================
# RESPONSE SCHEMAS
# ==========================================

class CompanyProfileResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    legal_name: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_branch: Optional[str] = None


class QuotationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    quotation_number: str
    version: int
    enquiry_id: int
    enquiry_number: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_type: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None
    customer_city: Optional[str] = None
    customer_state: Optional[str] = None
    customer_pincode: Optional[str] = None
    survey_id: Optional[int] = None
    survey_number: Optional[str] = None
    system_type: str
    capacity_kw: float
    total_product_cost: float
    installation_cost: float
    tax_amount: float
    gross_amount: float
    subsidy_estimate: float
    net_payable_amount: float
    status: str
    quotation_date: date
    valid_until: date
    terms_and_conditions: Optional[str] = None
    created_by: int
    creator_name: Optional[str] = None
    company_profile: Optional[CompanyProfileResponse] = None
    items: List[QuotationItemResponse] = []
    revisions: List[QuotationRevisionResponse] = []
    created_at: datetime
    updated_at: datetime


class QuotationListResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    items: List[QuotationResponse]
    total: int
    page: int
    limit: int
    pages: int
