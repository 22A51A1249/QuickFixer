"""Ticket Management Endpoints."""

from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query

from src.database.db_manager import DatabaseManager
from src.llm.triage_agent import SupportTriageAgent
from src.models.user import User, UserRole
from src.models.ticket import (
    Ticket,
    TicketCategory,
    TicketPriority,
    TicketStatus,
    TicketMessage,
)
from src.auth.permissions import can_view_ticket, can_update_ticket, can_assign_ticket
from backend.dependencies import get_db, get_agent, get_current_user, require_technician_or_admin
from backend.schemas.ticket import (
    TicketCreateRequest,
    TicketUpdateRequest,
    TicketNoteRequest,
    TicketResponse,
    TicketMessageResponse,
    TriagePreviewRequest,
    TriagePreviewResponse,
)

router = APIRouter(prefix="/api/tickets", tags=["Ticket Operations"])


def _ticket_to_response(t: Ticket) -> TicketResponse:
    return TicketResponse(
        id=t.id,
        title=t.title,
        description=t.description,
        category=t.category.value if isinstance(t.category, TicketCategory) else str(t.category),
        priority=t.priority.value if isinstance(t.priority, TicketPriority) else str(t.priority),
        status=t.status.value if isinstance(t.status, TicketStatus) else str(t.status),
        user_name=t.user_name,
        user_email=t.user_email,
        device_info=t.device_info,
        ai_diagnosis=t.ai_diagnosis,
        suggested_steps=t.suggested_steps,
        assigned_to=t.assigned_to,
        resolution_notes=t.resolution_notes,
        created_at=t.created_at,
        updated_at=t.updated_at,
        resolved_at=t.resolved_at,
    )


@router.get("", response_model=List[TicketResponse])
async def list_tickets(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Retrieve tickets scoped to current user's role and authorization."""
    tickets = db.list_tickets_for_user(
        user=current_user,
        status=status if status and status != "All" else None,
        priority=priority if priority and priority != "All" else None,
        category=category if category and category != "All" else None,
        search_query=search.strip() if search and search.strip() else None,
    )
    return [_ticket_to_response(t) for t in tickets]


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    req: TicketCreateRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
    agent: SupportTriageAgent = Depends(get_agent),
):
    """Submit a new ticket with automatic AI triage and category/priority prediction."""
    # Determine category, priority, and diagnostic actions via triage
    triage = agent.triage_ticket(req.description)

    # Use specified values or fallback to AI-predicted values
    final_category = triage.category
    if req.category and req.category != "Auto-Detect":
        for c in TicketCategory:
            if c.value.lower() == req.category.lower():
                final_category = c
                break

    final_priority = triage.priority
    if req.priority and req.priority != "Auto-Detect":
        for p in TicketPriority:
            if p.value.lower() == req.priority.lower():
                final_priority = p
                break

    new_ticket = Ticket(
        id="",
        title=req.title,
        description=req.description,
        category=final_category,
        priority=final_priority,
        status=TicketStatus.OPEN,
        user_name=current_user.full_name,
        user_email=current_user.email,
        device_info=req.device_info or "Windows 11 Enterprise",
        assigned_to=triage.recommended_team,
        ai_diagnosis=f"Triage Assessment: {triage.recommended_team}. Confidence: {triage.confidence:.0%}",
        suggested_steps="\n".join([f"- {a}" for a in triage.immediate_actions]),
    )

    created = db.create_ticket(new_ticket)
    return _ticket_to_response(created)


@router.post("/triage-preview", response_model=TriagePreviewResponse)
async def triage_preview(
    req: TriagePreviewRequest,
    current_user: User = Depends(get_current_user),
    agent: SupportTriageAgent = Depends(get_agent),
):
    """Live AI analysis and classification of problem description without creating a ticket."""
    triage = agent.triage_ticket(req.description)
    return TriagePreviewResponse(
        category=triage.category.value,
        priority=triage.priority.value,
        summary=triage.summary,
        confidence=triage.confidence,
        key_entities=triage.key_entities,
        immediate_actions=triage.immediate_actions,
        recommended_team=triage.recommended_team,
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket_details(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Fetch ticket details if authorized."""
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found.",
        )

    if not can_view_ticket(current_user, ticket):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You do not have permission to view this ticket.",
        )

    return _ticket_to_response(ticket)


@router.get("/{ticket_id}/messages", response_model=List[TicketMessageResponse])
async def get_ticket_messages(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Fetch all communication thread messages for a ticket."""
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

    if not can_view_ticket(current_user, ticket):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied.")

    messages = db.get_messages(ticket_id)
    return [
        TicketMessageResponse(
            id=m.id,
            ticket_id=m.ticket_id,
            sender=m.sender,
            message=m.message,
            timestamp=m.timestamp,
        )
        for m in messages
    ]


@router.post("/{ticket_id}/messages", response_model=TicketMessageResponse)
async def add_ticket_message(
    ticket_id: str,
    req: TicketNoteRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Add a message or internal note to a ticket thread."""
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

    if not can_view_ticket(current_user, ticket):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied.")

    sender_label = "user"
    if current_user.is_admin:
        sender_label = "admin"
    elif current_user.role == UserRole.TECHNICIAN:
        sender_label = "technician"

    msg = TicketMessage(
        ticket_id=ticket.id,
        sender=sender_label,
        message=req.message,
        timestamp=datetime.now().isoformat(),
    )
    msg_id = db.add_message(msg)
    msg.id = msg_id

    return TicketMessageResponse(
        id=msg.id,
        ticket_id=msg.ticket_id,
        sender=msg.sender,
        message=msg.message,
        timestamp=msg.timestamp,
    )


@router.patch("/{ticket_id}/status", response_model=TicketResponse)
async def update_ticket_status(
    ticket_id: str,
    req: TicketUpdateRequest,
    current_user: User = Depends(require_technician_or_admin),
    db: DatabaseManager = Depends(get_db),
):
    """Update ticket lifecycle state, priority, assignee, or resolution notes."""
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

    if not can_update_ticket(current_user, ticket):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied.")

    if req.status:
        try:
            ticket.status = TicketStatus(req.status)
        except ValueError:
            for s in TicketStatus:
                if s.value.lower() == req.status.lower():
                    ticket.status = s
                    break

    if req.priority:
        try:
            ticket.priority = TicketPriority(req.priority)
        except ValueError:
            for p in TicketPriority:
                if p.value.lower() == req.priority.lower():
                    ticket.priority = p
                    break

    if req.assigned_to is not None:
        if not can_assign_ticket(current_user, ticket) and current_user.role == UserRole.TECHNICIAN:
            # Technicians can assign tickets to themselves
            if current_user.full_name.lower() in req.assigned_to.lower() or current_user.username in req.assigned_to:
                ticket.assigned_to = req.assigned_to
            else:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admins can reassign between other technicians.")
        else:
            ticket.assigned_to = req.assigned_to

    if req.resolution_notes is not None:
        ticket.resolution_notes = req.resolution_notes

    updated = db.update_ticket(ticket)
    return _ticket_to_response(updated)


@router.post("/{ticket_id}/generate-summary")
async def generate_resolution_summary(
    ticket_id: str,
    current_user: User = Depends(require_technician_or_admin),
    db: DatabaseManager = Depends(get_db),
    agent: SupportTriageAgent = Depends(get_agent),
):
    """Draft formal resolution notes using AI for technician reviewing ticket."""
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

    messages = db.get_messages(ticket_id)
    summary = agent.generate_resolution_summary(ticket, messages)
    return {"resolution_summary": summary}

