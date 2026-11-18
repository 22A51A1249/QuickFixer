"""User and admin schemas."""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3)
    email: str = Field(..., min_length=5)
    full_name: str = Field(..., min_length=2)
    password: str = Field(..., min_length=6)
    role: str = Field(..., description="'employee', 'technician', or 'admin'")
    team: Optional[str] = None


class UserStatusUpdateRequest(BaseModel):
    is_active: bool


class UserRoleUpdateRequest(BaseModel):
    role: str
    team: Optional[str] = None


class AuditLogResponse(BaseModel):
    id: Optional[int] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: str

