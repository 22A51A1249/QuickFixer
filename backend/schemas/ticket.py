"""Ticket and incident lifecycle schemas."""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class TicketCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, description="Incident title or brief summary")
    description: str = Field(..., min_length=5, description="Detailed problem description")
    category: Optional[str] = Field(None, description="Ticket category (optional, auto-triaged if omitted)")
    priority: Optional[str] = Field(None, description="Ticket priority (optional, auto-triaged if omitted)")
    device_info: Optional[str] = Field(None, description="Device and OS environment")


class TicketUpdateRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None


class TicketNoteRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Technician or employee message")


class TicketMessageResponse(BaseModel):
    id: Optional[int] = None
    ticket_id: str
    sender: str
    message: str
    timestamp: str


class TicketResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    priority: str
    status: str
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    device_info: Optional[str] = None
    ai_diagnosis: Optional[str] = None
    suggested_steps: Optional[str] = None
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: str
    updated_at: str
    resolved_at: Optional[str] = None


class TriagePreviewRequest(BaseModel):
    description: str = Field(..., min_length=3)


class TriagePreviewResponse(BaseModel):
    category: str
    priority: str
    summary: str
    confidence: float
    key_entities: List[str] = Field(default_factory=list)
    immediate_actions: List[str] = Field(default_factory=list)
    recommended_team: str

