"""Session Manager for secure state tracking, inactivity timeouts, and user context."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from config import settings
from src.models.user import User


class SessionManager:
    """Manages authenticated user sessions across Streamlit reruns and backend services."""

    SESSION_KEY = "apex_auth_session"
    _in_memory_sessions: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def _get_storage(cls) -> Optional[Any]:
        """Access Streamlit session_state safely if in a Streamlit context."""
        try:
            import streamlit as st
            # Verify streamlit is actively running with session_state
            if hasattr(st, "session_state"):
                return st.session_state
        except Exception:
            pass
        return None

    @classmethod
    def login_user(cls, user: User, ip_address: str = "127.0.0.1") -> str:
        """Initialize an authenticated session for the specified user."""
        token = f"sess_{uuid.uuid4().hex}"
        now = datetime.now()
        session_data = {
            "token": token,
            "user": user,
            "ip_address": ip_address,
            "login_time": now.isoformat(),
            "last_activity": now.isoformat(),
        }

        storage = cls._get_storage()
        if storage is not None:
            storage[cls.SESSION_KEY] = session_data

        cls._in_memory_sessions[token] = session_data
        cls._in_memory_sessions["active_test_token"] = session_data
        return token

    @classmethod
    def get_session_data(cls) -> Optional[Dict[str, Any]]:
        """Retrieve current session metadata, verifying inactivity timeout."""
        storage = cls._get_storage()
        data = None

        # When running in Streamlit, check ONLY the current browser's session_state
        if storage is not None:
            if cls.SESSION_KEY in storage:
                data = storage[cls.SESSION_KEY]
        else:
            # Headless scripts / pytest test runner without Streamlit
            if "active_test_token" in cls._in_memory_sessions:
                data = cls._in_memory_sessions["active_test_token"]

        if not data:
            return None

        # Inactivity timeout validation
        last_act_str = data.get("last_activity")
        if last_act_str:
            try:
                last_act = datetime.fromisoformat(last_act_str)
                if datetime.now() - last_act > timedelta(minutes=settings.SESSION_EXPIRY_MINUTES):
                    cls.logout_user()
                    return None
            except Exception:
                pass

        # Update last activity
        data["last_activity"] = datetime.now().isoformat()
        return data

    @classmethod
    def get_current_user(cls) -> Optional[User]:
        """Retrieve the currently authenticated User instance."""
        data = cls.get_session_data()
        if not data:
            return None
        user: Optional[User] = data.get("user")
        if user and not user.is_active:
            # Account was deactivated during session
            cls.logout_user()
            return None
        return user

    @classmethod
    def is_authenticated(cls) -> bool:
        """Check if there is an active, valid authenticated user session."""
        return cls.get_current_user() is not None

    @classmethod
    def logout_user(cls) -> None:
        """Invalidate the session and clear all authentication tokens and state."""
        storage = cls._get_storage()
        if storage is not None and cls.SESSION_KEY in storage:
            del storage[cls.SESSION_KEY]

        cls._in_memory_sessions.pop("active_test_token", None)

