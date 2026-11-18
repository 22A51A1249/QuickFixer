"""Conversational AI & IT Support Assistant Endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from src.database.db_manager import DatabaseManager
from src.llm.triage_agent import SupportTriageAgent
from src.models.user import User
from src.models.ticket import Ticket, TicketStatus, TicketFeedback
from backend.dependencies import get_db, get_agent, get_current_user
from backend.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatFeedbackRequest,
    ChatEscalateRequest,
    SourceCitation,
)
from backend.schemas.ticket import TicketResponse

router = APIRouter(prefix="/api/chat", tags=["AI IT Chat Assistant"])


@router.post("/message", response_model=ChatMessageResponse)
async def send_chat_message(
    req: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    agent: SupportTriageAgent = Depends(get_agent),
):
    """Process employee IT inquiry through stateful LangGraph agent, domain guardrails, and RAG."""
    session_id = req.session_id or f"sess_{current_user.id}_{uuid.uuid4().hex[:8]}"

    # Execute agentic pipeline
    result = agent.answer_query(
        user_message=req.message,
        conversation_history=req.conversation_history,
        session_id=session_id,
    )

    sources = [
        SourceCitation(
            source=s.get("source", "knowledge_base"),
            title=s.get("title", "Runbook Article"),
            score=float(s.get("score", 0.0)),
            snippet=s.get("snippet", ""),
        )
        for s in result.get("sources", [])
    ]

    return ChatMessageResponse(
        answer=result.get("answer", "No response generated."),
        sources=sources,
        used_gemini=result.get("used_gemini", False),
        query_type=result.get("query_type", "troubleshooting"),
        approval_status=result.get("approval_status"),
        ticket_id=result.get("ticket_id"),
        assigned_team=result.get("assigned_team"),
        session_id=session_id,
    )


@router.post("/escalate", response_model=TicketResponse)
async def escalate_chat_to_ticket(
    req: ChatEscalateRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
    agent: SupportTriageAgent = Depends(get_agent),
):
    """Escalate an ongoing chat conversation into a formal IT Support Ticket with automated triage."""
    # Combine user turns from conversation history
    user_turns = [m.get("content", "") for m in req.conversation_history if m.get("role") == "user"]
    combined_desc = "\n\n".join(user_turns)
    if not combined_desc.strip():
        combined_desc = "Issue escalated from AI Chat session."

    triage = agent.triage_ticket(combined_desc)
    ticket_title = req.title or f"Chat Incident: {triage.summary}"

    new_ticket = Ticket(
        id="",
        title=ticket_title,
        description=combined_desc,
        category=triage.category,
        priority=triage.priority,
        status=TicketStatus.OPEN,
        user_name=current_user.full_name,
        user_email=current_user.email,
        device_info=req.device_info or "Corporate Device",
        assigned_to=triage.recommended_team,
        ai_diagnosis=f"Triage Team: {triage.recommended_team}. Confidence: {triage.confidence:.0%}",
        suggested_steps="\n".join([f"- {a}" for a in triage.immediate_actions]),
    )

    created = db.create_ticket(new_ticket)
    return TicketResponse(
        id=created.id,
        title=created.title,
        description=created.description,
        category=created.category.value,
        priority=created.priority.value,
        status=created.status.value,
        user_name=created.user_name,
        user_email=created.user_email,
        device_info=created.device_info,
        ai_diagnosis=created.ai_diagnosis,
        suggested_steps=created.suggested_steps,
        assigned_to=created.assigned_to,
        resolution_notes=created.resolution_notes,
        created_at=created.created_at,
        updated_at=created.updated_at,
        resolved_at=created.resolved_at,
    )


@router.post("/feedback")
async def submit_chat_feedback(
    req: ChatFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Submit CSAT satisfaction rating and feedback."""
    target_ticket_id = req.ticket_id or "CHAT-GENERAL"
    feedback = TicketFeedback(
        ticket_id=target_ticket_id,
        rating=req.rating,
        comments=req.comments or f"CSAT from {current_user.username}",
        resolved_by_ai=True,
        created_at=datetime.now().isoformat(),
    )
    db.add_feedback(feedback)
    return {"message": "Feedback submitted successfully. Thank you!"}

