"""User Management and Security Audit Log Endpoints (Admin Only)."""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from src.database.db_manager import DatabaseManager
from src.auth.auth_manager import AuthManager
from src.models.user import User, UserRole, AuditLogEntry
from backend.dependencies import get_db, get_auth, require_admin
from backend.schemas.auth import UserResponse
from backend.schemas.user import (
    UserCreateRequest,
    UserStatusUpdateRequest,
    UserRoleUpdateRequest,
    AuditLogResponse,
)

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])


def _user_to_response(u: User) -> UserResponse:
    return UserResponse(
        id=u.id,
        username=u.username,
        email=u.email,
        full_name=u.full_name,
        role=u.role.value,
        team=u.team,
        is_active=u.is_active,
        id_badge_label=u.id_badge_label,
        created_at=u.created_at,
    )


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    role: Optional[str] = Query(None),
    current_admin: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db),
):
    """Retrieve all corporate user accounts."""
    users = db.list_users(role=role)
    return [_user_to_response(u) for u in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    req: UserCreateRequest,
    current_admin: User = Depends(require_admin),
    auth: AuthManager = Depends(get_auth),
):
    """Create a new employee or technician account with initial credentials."""
    try:
        role_enum = UserRole(req.role.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{req.role}'. Must be 'employee', 'technician', or 'admin'.",
        )

    success, new_user, message = auth.create_user(
        username=req.username,
        email=req.email,
        full_name=req.full_name,
        password=req.password,
        role=role_enum,
        team=req.team,
        created_by=current_admin,
    )

    if not success or not new_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return _user_to_response(new_user)


@router.patch("/users/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: str,
    req: UserStatusUpdateRequest,
    current_admin: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db),
):
    """Activate or deactivate a user account."""
    target_user = db.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if target_user.id == current_admin.id and not req.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot deactivate your own admin account.")

    db.update_user_status(user_id, req.is_active)
    updated = db.get_user_by_id(user_id)
    return _user_to_response(updated)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    req: UserRoleUpdateRequest,
    current_admin: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db),
):
    """Update role or team assignment for a user."""
    target_user = db.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    try:
        role_enum = UserRole(req.role.lower())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role.")

    db.update_user_role(user_id, role_enum, team=req.team)
    updated = db.get_user_by_id(user_id)
    return _user_to_response(updated)


@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    current_admin: User = Depends(require_admin),
    db: DatabaseManager = Depends(get_db),
):
    """Retrieve security and authentication audit events."""
    logs = db.list_audit_logs(limit=limit)
    return [
        AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            username=log.username,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            ip_address=log.ip_address,
            timestamp=log.timestamp,
        )
        for log in logs
    ]

