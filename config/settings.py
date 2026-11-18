"""Centralized settings and environment configuration for QuickFixer."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment configuration
load_dotenv(BASE_DIR / ".env")


class Settings:
    """Centralized application settings."""

    # Project directories
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    KNOWLEDGE_BASE_DIR: Path = BASE_DIR / os.getenv("KNOWLEDGE_BASE_DIR", "data/knowledge_base")
    VECTOR_INDEX_DIR: Path = BASE_DIR / os.getenv("VECTOR_INDEX_DIR", "data/vector_store")
    SQLITE_DB_PATH: Path = BASE_DIR / os.getenv("SQLITE_DB_PATH", "data/tickets.db")
    CHECKPOINT_DB_PATH: Path = BASE_DIR / os.getenv("CHECKPOINT_DB_PATH", "data/checkpoints.db")

    # Google Gemini settings (Free-tier compatible default)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", "").strip() or None
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    GEMINI_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.1"))
    GEMINI_TIMEOUT: int = int(os.getenv("GEMINI_TIMEOUT", "30"))
    GEMINI_MAX_RETRIES: int = int(os.getenv("GEMINI_MAX_RETRIES", "2"))

    # RAG & Embedding settings
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "120"))
    TOP_K_RETRIEVAL: int = int(os.getenv("TOP_K_RETRIEVAL", "4"))
    SIMILARITY_SCORE_THRESHOLD: float = float(os.getenv("SIMILARITY_SCORE_THRESHOLD", "0.7"))

    # Demo Mode & Offline Fallback settings
    ENABLE_OFFLINE_DEMO_FALLBACK: bool = (
        os.getenv("ENABLE_OFFLINE_DEMO_FALLBACK", "true").lower() in ("true", "1", "yes")
    )

    # Authentication & RBAC settings
    SESSION_EXPIRY_MINUTES: int = int(os.getenv("SESSION_EXPIRY_MINUTES", "60"))
    MAX_FAILED_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_FAILED_LOGIN_ATTEMPTS", "5"))
    LOCKOUT_DURATION_MINUTES: int = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "ApexAdmin2026!")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@company.com")

    @classmethod
    def ensure_directories(cls) -> None:
        """Create necessary directories if they do not exist."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
        cls.VECTOR_INDEX_DIR.mkdir(parents=True, exist_ok=True)
        cls.SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.CHECKPOINT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()

