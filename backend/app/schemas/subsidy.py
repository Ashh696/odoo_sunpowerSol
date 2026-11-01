from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from decimal import Decimal

VALID_SUBSIDY_STATUSES = {
    "DRAFT",
    "SUBMITTED_TO_DISCOM",
    "INSPECTION_SCHEDULED",
    "INSPECTION_COMPLETED",
    "APPROVED",
    "SUBSIDY_DISBURSED",
    "REJECTED",
}

VALID_SUBSIDY_DOC_TYPES = {
    "ELECTRICITY_BILL",
    "AADHAAR_CARD",
    "BANK_PASSBOOK",
    "JOINT_INSPECTION_REPORT",
    "NET_METER_INSTALL_REPORT",
    "VENDOR_DECLARATION",
    "PHOTOGRAPH_COMMISSIONING",
}

VALID_DOC_VERIFICATION_STATUSES = {
    "PENDING",
    "VERIFIED",
    "REJECTED",
}


# ==========================================
# 1. SUBSIDY APPLICATIONS
# ==========================================

class SubsidyApplicationCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    project_id: int = Field(..., gt=0)
    portal_registration_number: Optional[str] = Field(None, max_length=100)
    discom_name: str = Field(..., min_length=2, max_length=150)
    sanctioned_capacity_kw: Decimal = Field(..., gt=0)
    eligible_subsidy_amount: Optional[Decimal] = Field(None, ge=0)
    application_date: date = Field(default_factory=date.today)


class SubsidyApplicationUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    portal_registration_number: Optional[str] = Field(None, max_length=100)
    discom_name: Optional[str] = Field(None, min_length=2, max_length=150)
    sanctioned_capacity_kw: Optional[Decimal] = Field(None, gt=0)
    eligible_subsidy_amount: Optional[Decimal] = Field(None, ge=0)


class SubsidyStatusTransitionRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    status: str = Field(..., max_length=50)
    comments: Optional[str] = None
    rejection_reason: Optional[str] = None


# ==========================================
# 2. SUBSIDY DOCUMENTS
# ==========================================

class SubsidyDocumentUploadRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    document_type: str = Field(..., max_length=100)
    file_name: str = Field(..., min_length=3, max_length=255)
    file_path: Optional[str] = None
    remarks: Optional[str] = None


class SubsidyDocumentVerificationRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    verification_status: str = Field(..., max_length=50)
    remarks: Optional[str] = None


class SubsidyDocumentResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    subsidy_application_id: int
    document_type: str
    attachment_id: int
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    verification_status: str
    remarks: Optional[str] = None
    verified_by: Optional[int] = None
    verifier_name: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime


# ==========================================
# 3. SUBSIDY STATUS HISTORY
# ==========================================

class SubsidyStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    subsidy_application_id: int
    previous_status: Optional[str] = None
    new_status: str
    action_date: datetime
    comments: Optional[str] = None
    updated_by: int
    updater_name: Optional[str] = None
    created_at: datetime


# ==========================================
# 4. SUBSIDY DISBURSEMENT PAYMENTS
# ==========================================

class SubsidyPaymentCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    disbursement_date: date = Field(default_factory=date.today)
    disbursed_amount: Decimal = Field(..., gt=0)
    bank_reference_number: Optional[str] = Field(None, max_length=100)
    payment_reference: Optional[str] = Field(None, max_length=100)


class SubsidyPaymentResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    subsidy_application_id: int
    project_id: int
    payment_reference: str
    disbursement_date: date
    disbursed_amount: Decimal
    bank_reference_number: Optional[str] = None
    created_at: datetime


# ==========================================
# 5. FULL APPLICATION RESPONSES
# ==========================================

class SubsidyApplicationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    application_number: str
    project_id: int
    project_code: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    portal_registration_number: Optional[str] = None
    discom_name: str
    sanctioned_capacity_kw: Decimal
    eligible_subsidy_amount: Decimal
    application_date: date
    status: str
    rejection_reason: Optional[str] = None
    created_by: int
    creator_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SubsidyApplicationDetailResponse(SubsidyApplicationResponse):
    documents: List[SubsidyDocumentResponse] = []
    history: List[SubsidyStatusHistoryResponse] = []
    payments: List[SubsidyPaymentResponse] = []
