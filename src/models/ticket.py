"""Data models and schemas for the IT Support and Ticket Resolution System."""

from __future__ import annotations

from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class TicketCategory(str, Enum):
    NETWORK = "Network & Connectivity"
    HARDWARE = "Hardware & Peripherals"
    SOFTWARE = "Software & Applications"
    SECURITY = "Security & Access"
    ACCOUNT = "Account & Authentication"
    EMAIL = "Email & Collaboration"
    OTHER = "General IT Inquiry"


class TicketPriority(str, Enum):
    CRITICAL = "Critical"  # Complete business outage, security breach, VIP affected
    HIGH = "High"          # Work blocked, multiple users impacted, urgent deadline
    MEDIUM = "Medium"      # Normal issue with workaround, single user impacted
    LOW = "Low"            # Minor inconvenience, general question, request for info


class TicketStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    WAITING_ON_USER = "Waiting on User"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class TicketMessage(BaseModel):
    """A message in a ticket's audit/conversation log."""
    id: Optional[int] = None
    ticket_id: str
    sender: str  # "user", "ai_assistant", "technician", "system"
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class Ticket(BaseModel):
    """Complete representation of an IT support ticket."""
    id: str
    title: str
    description: str
    category: TicketCategory = TicketCategory.OTHER
    priority: TicketPriority = TicketPriority.MEDIUM
    status: TicketStatus = TicketStatus.OPEN
    user_name: str = "Employee"
    user_email: str = "user@company.com"
    device_info: Optional[str] = "Windows 11 / Enterprise Workstation"
    ai_diagnosis: Optional[str] = None
    suggested_steps: Optional[str] = None
    assigned_to: Optional[str] = "Unassigned"
    resolution_notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    resolved_at: Optional[str] = None


class TriageResult(BaseModel):
    """Structured output from LLM triage classification."""
    category: TicketCategory
    priority: TicketPriority
    summary: str
    confidence: float = 0.95
    key_entities: List[str] = Field(default_factory=list)
    immediate_actions: List[str] = Field(default_factory=list)
    recommended_team: str = "Tier 1 Service Desk"


class TicketFeedback(BaseModel):
    """User feedback for ticket resolution quality."""
    ticket_id: str
    rating: int  # 1 to 5 stars
    comments: Optional[str] = ""
    resolved_by_ai: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

