"""User and Audit Log domain models for QuickFixer Authentication and RBAC."""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """Supported authorization roles in QuickFixer."""
    EMPLOYEE = "employee"
    TECHNICIAN = "technician"
    ADMIN = "admin"


class User(BaseModel):
    """Authenticated user representation across backend, services, and UI."""
    id: str
    username: str
    email: str
    full_name: str
    role: UserRole
    team: Optional[str] = None
    is_active: bool = True
    created_at: str
    updated_at: str

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def is_technician(self) -> bool:
        return self.role in (UserRole.TECHNICIAN, UserRole.ADMIN)

    @property
    def is_employee(self) -> bool:
        return self.role == UserRole.EMPLOYEE

    @property
    def employee_id(self) -> str:
        return self.id if self.role == UserRole.EMPLOYEE else ""

    @property
    def technician_id(self) -> str:
        return self.id if self.role == UserRole.TECHNICIAN else ""

    @property
    def id_badge_label(self) -> str:
        if self.role == UserRole.EMPLOYEE:
            return f"Employee ID: {self.id}"
        elif self.role == UserRole.TECHNICIAN:
            return f"Technician ID: {self.id}"
        return f"Admin ID: {self.id}"


class AuditLogEntry(BaseModel):
    """Security audit record for compliance and activity inspection."""
    id: Optional[int] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = "127.0.0.1"
    timestamp: str

