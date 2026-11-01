from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from decimal import Decimal

VALID_SYSTEM_TYPES = {"ON_GRID", "OFF_GRID", "HYBRID"}


class BomItemBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    product_id: int = Field(..., description="ID of the equipment catalog product")
    item_category: Optional[str] = Field(None, max_length=100, description="Equipment category (defaults to product category)")
    default_quantity: Decimal = Field(..., gt=0, description="Default unit quantity (> 0)")
    unit_of_measure: Optional[str] = Field(None, max_length=50, description="Unit of measure (must match product UOM)")
    is_mandatory: bool = Field(True, description="Whether this component is mandatory in standard configuration")


class BomItemCreate(BomItemBase):
    pass


class BomItemUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    default_quantity: Optional[Decimal] = Field(None, gt=0, description="Updated default quantity (> 0)")
    unit_of_measure: Optional[str] = Field(None, max_length=50)
    is_mandatory: Optional[bool] = None
    item_category: Optional[str] = Field(None, max_length=100)


class BomItemResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    bom_template_id: int
    product_id: int
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    brand: Optional[str] = None
    model_number: Optional[str] = None
    wattage_or_capacity: Optional[str] = None
    item_category: str
    default_quantity: float
    unit_of_measure: str
    is_mandatory: bool
    unit_price: Optional[float] = None
    is_product_active: Optional[bool] = None
    created_at: datetime


class BomTemplateBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    template_name: str = Field(..., min_length=1, max_length=150, description="Unique template name")
    system_type: str = Field(..., description="ON_GRID, OFF_GRID, HYBRID")
    capacity_kw: Decimal = Field(..., gt=0, description="System capacity in kW (e.g. 1.0, 2.0, 3.0, 4.0, 5.0)")
    description: Optional[str] = Field(None, max_length=2000, description="Technical engineering notes or description")
    is_active: bool = Field(True, description="Whether template is active for new BOM generation")

    @field_validator("template_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Template name cannot be empty or whitespace only")
        return clean

    @field_validator("system_type")
    @classmethod
    def validate_system_type(cls, v: str) -> str:
        clean = v.strip().upper()
        if clean not in VALID_SYSTEM_TYPES:
            raise ValueError(f"system_type must be one of {VALID_SYSTEM_TYPES}")
        return clean


class BomTemplateCreate(BomTemplateBase):
    items: Optional[List[BomItemCreate]] = Field(default_factory=list, description="Optional initial list of BOM items")


class BomTemplateUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    template_name: Optional[str] = Field(None, min_length=1, max_length=150)
    system_type: Optional[str] = None
    capacity_kw: Optional[Decimal] = Field(None, gt=0)
    description: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("template_name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            if not clean:
                raise ValueError("Template name cannot be empty or whitespace only")
            return clean
        return None

    @field_validator("system_type")
    @classmethod
    def validate_system_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().upper()
            if clean not in VALID_SYSTEM_TYPES:
                raise ValueError(f"system_type must be one of {VALID_SYSTEM_TYPES}")
            return clean
        return None


class BomTemplateStatusUpdate(BaseModel):
    is_active: bool = Field(..., description="Target active status for BOM template")


class BomTemplateResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    template_name: str
    system_type: str
    capacity_kw: float
    description: Optional[str] = None
    is_active: bool
    created_by: int
    creator_name: Optional[str] = None
    item_count: int = 0
    created_at: datetime
    updated_at: datetime


class BomTemplateDetailResponse(BomTemplateResponse):
    items: List[BomItemResponse] = []


class BomTemplateListResponse(BaseModel):
    items: List[BomTemplateResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# ==========================================
# PROJECT BOM SCHEMAS
# ==========================================

class ProjectBomGenerateRequest(BaseModel):
    template_id: int = Field(..., description="ID of the active BOM template to generate project BOM from")


class ProjectBomItemUpdate(BaseModel):
    planned_quantity: Decimal = Field(..., ge=0, description="Updated planned quantity (>= 0 and >= allocated)")


class ProjectBomItemResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    project_id: int
    product_id: int
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    brand: Optional[str] = None
    item_category: str
    planned_quantity: float
    allocated_quantity: float
    dispatched_quantity: float
    installed_quantity: float
    unit_cost_snapshot: float
    total_planned_cost: float
    created_at: datetime
    updated_at: datetime


class ProjectBomListResponse(BaseModel):
    project_id: int
    project_code: str
    system_type: str
    system_capacity_kw: float
    items: List[ProjectBomItemResponse]
    total_items: int
    total_estimated_cost: float
