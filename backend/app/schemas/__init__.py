from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    success: bool = True
    message: str = "Success"
    data: Optional[DataT] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DatabaseHealth(BaseModel):
    connected: bool
    dialect: Optional[str] = None
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    app_name: str
    status: str
    environment: str
    database: DatabaseHealth
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserProfileResponse,
    RoleInfo,
    ChangePasswordRequest,
)

__all__ = [
    "APIResponse",
    "DatabaseHealth",
    "HealthResponse",
    "LoginRequest",
    "TokenResponse",
    "UserProfileResponse",
    "RoleInfo",
    "ChangePasswordRequest",
]
