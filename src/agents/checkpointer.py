"""Persistent SQLite Checkpointer for LangGraph Workflow State."""

from __future__ import annotations

import sqlite3
from typing import Optional
from langgraph.checkpoint.sqlite import SqliteSaver
from config.settings import settings

_saver: Optional[SqliteSaver] = None
_conn: Optional[sqlite3.Connection] = None


def get_checkpointer() -> SqliteSaver:
    """Initialize or return the singleton SqliteSaver checkpointer."""
    global _saver, _conn
    if _saver is None:
        settings.CHECKPOINT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(
            str(settings.CHECKPOINT_DB_PATH),
            check_same_thread=False,
        )
        _saver = SqliteSaver(_conn)
    return _saver

