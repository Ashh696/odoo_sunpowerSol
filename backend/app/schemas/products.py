from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from decimal import Decimal

# Canonical product categories documented in the system
VALID_PRODUCT_CATEGORIES = {
    "SOLAR_PANEL",
    "INVERTER",
    "BATTERY",
    "STRUCTURE",
    "CABLES",
    "DCDB",
    "ACDB",
    "LIGHTNING_ARRESTER",
    "EARTHING",
    "MISC",
}

VALID_UNITS_OF_MEASURE = {"NOS", "METERS", "SETS", "KG", "FEET", "ROLLS"}


class ProductBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: str = Field(..., min_length=1, max_length=255, description="Full product / component description")
    category: str = Field(..., min_length=1, max_length=100, description="Equipment category")
    brand: Optional[str] = Field(None, max_length=100, description="Manufacturer or brand name")
    model_number: Optional[str] = Field(None, max_length=150, description="OEM model number or part code")
    wattage_or_capacity: Optional[str] = Field(None, max_length=100, description="Capacity / wattage spec (e.g. 550W, 5kW, 150Ah)")
    unit_of_measure: str = Field("NOS", max_length=50, description="UOM e.g. NOS, METERS, SETS, KG")
    is_serialized: bool = Field(False, description="Whether each physical unit is tracked by unique serial number")
    base_price: Decimal = Field(..., ge=0, description="Base unit catalogue price before tax (INR)")
    tax_rate_percent: Decimal = Field(Decimal("12.00"), ge=0, le=100, description="Applicable GST rate percent")
    min_stock_alert: Decimal = Field(Decimal("5.00"), ge=0, description="Minimum inventory threshold before reorder warning")
    is_active: bool = Field(True, description="Whether product is active for BOM and Quotation selection")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Product name cannot be empty or blank")
        return clean

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        clean = v.strip().upper()
        if not clean:
            raise ValueError("Product category cannot be empty")
        return clean

    @field_validator("unit_of_measure")
    @classmethod
    def validate_uom(cls, v: str) -> str:
        clean = v.strip().upper()
        if not clean:
            return "NOS"
        return clean

    @field_validator("brand", "model_number", "wattage_or_capacity")
    @classmethod
    def clean_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            return clean if clean else None
        return None


class ProductCreate(ProductBase):
    product_code: str = Field(..., min_length=1, max_length=100, description="Unique SKU or product code")

    @field_validator("product_code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        clean = v.strip().upper()
        if not clean:
            raise ValueError("Product code cannot be empty")
        return clean


class ProductUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    product_code: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    model_number: Optional[str] = Field(None, max_length=150)
    wattage_or_capacity: Optional[str] = Field(None, max_length=100)
    unit_of_measure: Optional[str] = Field(None, max_length=50)
    is_serialized: Optional[bool] = None
    base_price: Optional[Decimal] = Field(None, ge=0)
    tax_rate_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    min_stock_alert: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None

    @field_validator("product_code")
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().upper()
            if not clean:
                raise ValueError("Product code cannot be empty")
            return clean
        return None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            if not clean:
                raise ValueError("Product name cannot be empty or blank")
            return clean
        return None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().upper()
            if not clean:
                raise ValueError("Product category cannot be empty")
            return clean
        return None

    @field_validator("unit_of_measure")
    @classmethod
    def validate_uom(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip().upper()
            return clean if clean else "NOS"
        return None

    @field_validator("brand", "model_number", "wattage_or_capacity")
    @classmethod
    def clean_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            clean = v.strip()
            return clean if clean else None
        return None


class ProductStatusUpdate(BaseModel):
    is_active: bool = Field(..., description="Target active status for the product")


class ProductResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    product_code: str
    name: str
    category: str
    brand: Optional[str] = None
    model_number: Optional[str] = None
    wattage_or_capacity: Optional[str] = None
    unit_of_measure: str
    is_serialized: bool
    base_price: float
    tax_rate_percent: float
    min_stock_alert: float
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    limit: int
    total_pages: int
