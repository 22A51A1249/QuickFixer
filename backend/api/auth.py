"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from config import settings
from src.database.db_manager import DatabaseManager
from src.auth.auth_manager import AuthManager
from src.models.user import User, AuditLogEntry
from backend.dependencies import (
    get_db,
    get_auth,
    get_current_user,
    create_access_token,
)
from backend.schemas.auth import LoginRequest, LoginResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


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


@router.post("/login", response_model=LoginResponse)
async def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    auth: AuthManager = Depends(get_auth),
    db: DatabaseManager = Depends(get_db),
):
    """Authenticate corporate credentials and issue JWT."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    success, user, message = auth.authenticate(
        username_or_email=req.username_or_email,
        password=req.password,
        role=req.role,
        custom_id=req.custom_id,
        team=req.team,
        ip_address=client_ip,
        allow_any=False,  # strict secure credential check
    )

    if not success or not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message or "Invalid username or password.",
        )

    # Generate JWT
    token_data = {
        "sub": user.id,
        "username": user.username,
        "role": user.role.value,
        "email": user.email,
    }
    access_token = create_access_token(data=token_data)

    # Set secure HttpOnly cookie for session handling
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.SESSION_EXPIRY_MINUTES * 60,
        samesite="lax",
    )

    return LoginResponse(
        token=access_token,
        token_type="bearer",
        user=_user_to_response(user),
        message=message,
    )


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Sign out the current user and revoke session cookie."""
    response.delete_cookie(key="access_token")
    db.add_audit_log(
        AuditLogEntry(
            user_id=current_user.id,
            username=current_user.username,
            action="LOGOUT",
            resource_type="auth",
            resource_id=current_user.id,
            details=f"User '{current_user.username}' logged out.",
        )
    )
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return currently authenticated user profile."""
    return _user_to_response(current_user)

