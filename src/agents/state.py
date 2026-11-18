"""Typed state definition for LangGraph IT Support Agentic Workflow."""

from __future__ import annotations

from typing import TypedDict, List, Dict, Any, Optional


class SupportState(TypedDict, total=False):
    """Strongly typed state carried through the LangGraph StateGraph nodes."""

    # User and session context
    user_id: str
    session_id: str
    user_name: str
    user_email: str
    device_info: str

    # User input and history
    question: str
    rewritten_query: str
    conversation_history: List[Dict[str, str]]

    # Routing and classification
    query_type: str  # "troubleshooting", "ticket_creation", "ticket_status", "general_inquiry", "security_incident", "out_of_scope"
    domain_classification: Dict[str, Any]
    is_out_of_scope: bool
    issue_category: str
    priority: str

    # Retrieval and RAG evidence
    retrieved_documents: List[Dict[str, Any]]
    retrieval_scores: List[float]

    # AI generation and verification
    generated_answer: str
    resolution_confirmed: Optional[bool]
    ticket_required: bool

    # Triage and routing details
    triage_summary: str
    key_entities: List[str]
    immediate_actions: List[str]
    assigned_team: Optional[str]

    # Human-in-the-loop approval & execution
    approval_status: str  # "pending", "approved", "rejected"
    ticket_id: Optional[str]

    # Diagnostic metadata
    error_message: Optional[str]
    execution_mode: str  # "gemini" or "offline"
    interrupted_for_approval: bool

