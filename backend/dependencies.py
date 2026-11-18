"""FastAPI dependencies, security, JWT authentication, and service singletons."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import settings
from src.database.db_manager import DatabaseManager
from src.auth.auth_manager import AuthManager
from src.rag.retriever import KnowledgeRetriever
from src.llm.gemini_client import GeminiClient
from src.llm.triage_agent import SupportTriageAgent
from src.models.user import User, UserRole

# Secret key & token parameters
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "quickfixer-enterprise-secret-key-2026-secure-jwt")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.SESSION_EXPIRY_MINUTES

# Singletons cache
_db_manager_instance: Optional[DatabaseManager] = None
_auth_manager_instance: Optional[AuthManager] = None
_retriever_instance: Optional[KnowledgeRetriever] = None
_gemini_client_instance: Optional[GeminiClient] = None
_agent_instance: Optional[SupportTriageAgent] = None

security_bearer = HTTPBearer(auto_error=False)


def get_db() -> DatabaseManager:
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager()
    return _db_manager_instance


def get_auth(db: DatabaseManager = Depends(get_db)) -> AuthManager:
    global _auth_manager_instance
    if _auth_manager_instance is None:
        _auth_manager_instance = AuthManager(db=db)
    return _auth_manager_instance


def get_retriever() -> KnowledgeRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = KnowledgeRetriever()
    return _retriever_instance


def get_gemini() -> GeminiClient:
    global _gemini_client_instance
    if _gemini_client_instance is None:
        _gemini_client_instance = GeminiClient()
    return _gemini_client_instance


def get_agent(
    retriever: KnowledgeRetriever = Depends(get_retriever),
    gemini: GeminiClient = Depends(get_gemini),
) -> SupportTriageAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = SupportTriageAgent(retriever=retriever, gemini_client=gemini)
    return _agent_instance


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Encode user claims into a signed HS256 JWT."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a signed JWT."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception:
        return None


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: DatabaseManager = Depends(get_db),
) -> User:
    """Validate bearer token from Authorization header or cookie and return User."""
    token: Optional[str] = None
    if credentials:
        token = credentials.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token does not exist.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account has been deactivated. Contact an administrator.",
        )

    return user


async def require_technician_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Ensure current user is either a Technician or an Administrator."""
    if current_user.role not in (UserRole.TECHNICIAN, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Technician or Administrator privileges required.",
        )
    return current_user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Ensure current user has Administrator role."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Administrator privileges required.",
        )
    return current_user

