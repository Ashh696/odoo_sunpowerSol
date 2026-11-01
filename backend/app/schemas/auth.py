from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255, description="Account email address")
    password: str = Field(..., min_length=1, description="Account password")


class RoleInfo(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: int
    email: str
    phone: Optional[str] = None
    full_name: str
    is_active: bool
    is_verified: bool
    last_login_at: Optional[datetime] = None
    role: RoleInfo
    permissions: List[str] = Field(default_factory=list)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserProfileResponse


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, description="New password, minimum 8 characters")


class CustomerRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255, description="Full customer name")
    email: EmailStr = Field(..., description="Customer email address")
    phone: str = Field(..., min_length=10, max_length=30, description="Customer phone number")
    password: str = Field(..., min_length=8, max_length=128, description="Password, minimum 8 characters")
    address: Optional[str] = Field(None, max_length=500, description="Installation site address")
    city: Optional[str] = Field("Local", max_length=100, description="City")
    state: Optional[str] = Field("State", max_length=100, description="State")
    pincode: Optional[str] = Field("000000", max_length=20, description="Postal pincode")
