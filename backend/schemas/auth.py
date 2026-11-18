"""Authentication and user schemas."""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Username or corporate email")
    password: str = Field(..., description="User password")
    role: Optional[str] = Field(None, description="Optional role preference")
    custom_id: Optional[str] = Field(None, description="Optional custom badge ID")
    team: Optional[str] = Field(None, description="Optional team")


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    team: Optional[str] = None
    is_active: bool
    id_badge_label: str
    created_at: Optional[str] = None


class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user: UserResponse
    message: str

