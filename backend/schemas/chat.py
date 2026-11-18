"""Chat and conversational AI schemas."""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Employee input message")
    conversation_history: Optional[List[Dict[str, str]]] = Field(default_factory=list)
    session_id: Optional[str] = Field(None, description="Session / LangGraph thread ID")


class SourceCitation(BaseModel):
    source: str
    title: str
    score: float
    snippet: str


class ChatMessageResponse(BaseModel):
    answer: str
    sources: List[SourceCitation] = Field(default_factory=list)
    used_gemini: bool = False
    query_type: str = "troubleshooting"
    approval_status: Optional[str] = None
    ticket_id: Optional[str] = None
    assigned_team: Optional[str] = None
    session_id: str


class ChatFeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="CSAT star rating 1-5")
    comments: Optional[str] = None
    session_id: Optional[str] = None
    ticket_id: Optional[str] = None


class ChatEscalateRequest(BaseModel):
    conversation_history: List[Dict[str, str]]
    title: Optional[str] = None
    device_info: Optional[str] = None

