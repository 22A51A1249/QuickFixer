"""Role-Based Access Control (RBAC) and ticket-level authorization policies."""

from __future__ import annotations

from typing import List, Union, Optional
from src.models.user import User, UserRole
from src.models.ticket import Ticket
from src.auth.session_manager import SessionManager


class AccessDeniedError(Exception):
    """Raised when an operation is attempted without sufficient authorization."""
    pass


def require_login() -> User:
    """Ensure the user is authenticated; returns the active User or raises AccessDeniedError."""
    user = SessionManager.get_current_user()
    if not user:
        raise AccessDeniedError("Access Denied: You must be logged in to access this resource.")
    return user


def require_role(allowed_roles: List[Union[UserRole, str]], user: Optional[User] = None) -> bool:
    """Enforce that the user possesses one of the designated roles."""
    current_user = user or require_login()
    role_values = [r.value if isinstance(r, UserRole) else str(r).lower() for r in allowed_roles]

    if current_user.role.value.lower() not in role_values:
        raise AccessDeniedError("Access Denied: You do not have permission to access this resource.")
    return True


def can_view_ticket(user: User, ticket: Ticket) -> bool:
    """Determine whether a user is authorized to read a specific ticket."""
    if not user or not user.is_active:
        return False

    # 1. Administrators have unrestricted read access
    if user.is_admin:
        return True

    # 2. Technicians can view tickets assigned to them, their team, or general queue
    if user.role == UserRole.TECHNICIAN:
        assigned = (ticket.assigned_to or "").lower()
        if not assigned or "tier 1" in assigned:
            return True
        if user.full_name.lower() in assigned or user.username.lower() in assigned:
            return True
        if user.team and user.team.lower() in assigned:
            return True
        if user.team:
            import re
            for w in re.split(r"[\s&,/-]+", user.team.lower()):
                if len(w) >= 4 and w not in ("support", "desk") and w in assigned:
                    return True
        return False

    # 3. Employees can ONLY view tickets they submitted
    user_email = user.email.lower()
    user_name = user.full_name.lower()
    ticket_email = (ticket.user_email or "").lower()
    ticket_name = (ticket.user_name or "").lower()

    return user_email == ticket_email or user_name == ticket_name or user.username.lower() == ticket_name


def can_update_ticket(user: User, ticket: Ticket) -> bool:
    """Determine whether a user is authorized to modify status, notes, or reply to a ticket."""
    if not user or not user.is_active:
        return False

    # Admin has universal update rights
    if user.is_admin:
        return True

    # Technician can update only if authorized to view
    if user.role == UserRole.TECHNICIAN:
        return can_view_ticket(user, ticket)

    # Employees cannot modify technician ticket attributes
    return False


def can_assign_ticket(user: User, ticket: Ticket) -> bool:
    """Only administrators are authorized to reassign ticket routing queues or technicians."""
    return user is not None and user.is_active and user.is_admin


def can_manage_users(user: User) -> bool:
    """Only administrators are authorized to create, update, or alter user accounts and roles."""
    return user is not None and user.is_active and user.is_admin
