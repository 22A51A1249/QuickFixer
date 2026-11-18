"""System diagnostics and configuration endpoints."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from config import settings
from src.database.db_manager import DatabaseManager
from src.rag.retriever import KnowledgeRetriever
from src.llm.gemini_client import GeminiClient
from src.models.user import User
from backend.dependencies import get_db, get_retriever, get_gemini, get_current_user, require_admin

router = APIRouter(prefix="/api/system", tags=["System & Settings"])


class SettingsUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    temperature: Optional[float] = None


@router.get("/health")
async def get_system_health(
    db: DatabaseManager = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_retriever),
    gemini: GeminiClient = Depends(get_gemini),
):
    """System health check and diagnostic connectivity."""
    kb_files = list(settings.KNOWLEDGE_BASE_DIR.glob("*.*")) if settings.KNOWLEDGE_BASE_DIR.exists() else []
    return {
        "status": "healthy",
        "app_name": "QuickFixer",
        "version": "3.0.0",
        "database": {
            "status": "connected",
            "path": str(settings.SQLITE_DB_PATH),
        },
        "vector_store": {
            "status": "active",
            "type": "FAISS (IndexFlatIP)",
            "chunks_loaded": len(retriever.vector_store.chunks),
            "indexed_runbooks": len(kb_files),
        },
        "ai_engine": {
            "gemini_online": gemini.is_configured(),
            "model": gemini.model_name or settings.GEMINI_MODEL,
            "offline_fallback_enabled": settings.ENABLE_OFFLINE_DEMO_FALLBACK,
        },
    }


@router.get("/settings")
async def get_settings(
    current_admin: User = Depends(require_admin),
    gemini: GeminiClient = Depends(get_gemini),
):
    """Get active system settings (Admin only)."""
    masked_key = ""
    if gemini.api_key:
        masked_key = gemini.api_key[:6] + "..." + gemini.api_key[-4:] if len(gemini.api_key) > 10 else "***"

    return {
        "gemini_configured": gemini.is_configured(),
        "gemini_api_key_masked": masked_key,
        "gemini_model": gemini.model_name or settings.GEMINI_MODEL,
        "temperature": settings.GEMINI_TEMPERATURE,
        "session_expiry_minutes": settings.SESSION_EXPIRY_MINUTES,
        "top_k_retrieval": settings.TOP_K_RETRIEVAL,
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
    }


@router.post("/settings")
async def update_settings(
    req: SettingsUpdateRequest,
    current_admin: User = Depends(require_admin),
    gemini: GeminiClient = Depends(get_gemini),
):
    """Update dynamic AI settings at runtime (Admin only)."""
    if req.gemini_api_key is not None:
        gemini.update_api_key(req.gemini_api_key.strip() if req.gemini_api_key else None)
    if req.gemini_model:
        gemini.model_name = req.gemini_model
    if req.temperature is not None:
        settings.GEMINI_TEMPERATURE = req.temperature

    return {"message": "Settings updated successfully."}

