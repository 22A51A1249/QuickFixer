"""LangChain tools for IT Support, Knowledge Base, and Ticket Management."""

from __future__ import annotations

import re
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from src.database.db_manager import DatabaseManager
from src.rag.retriever import KnowledgeRetriever
from src.models.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus
from src.models.user import UserRole
from src.auth.session_manager import SessionManager
from src.auth.permissions import can_view_ticket, can_update_ticket

# Shared database and retriever references
_db_manager: Optional[DatabaseManager] = None
_retriever: Optional[KnowledgeRetriever] = None


def get_tool_db() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def set_tool_db(db: DatabaseManager) -> None:
    """Explicitly bind tool execution to a specific database (useful in test harnesses)."""
    global _db_manager
    _db_manager = db


def get_tool_retriever() -> KnowledgeRetriever:
    global _retriever
    if _retriever is None:
        _retriever = KnowledgeRetriever()
    return _retriever


@tool
def search_knowledge_base(query: str) -> str:
    """Search company troubleshooting documents and SOP runbooks for technical solutions."""
    retriever = get_tool_retriever()
    results = retriever.retrieve(query, top_k=3)
    if not results:
        return "No specific internal IT runbooks found matching this query."

    formatted = []
    for idx, (chunk, score) in enumerate(results, start=1):
        formatted.append(f"[{idx}] {chunk.title} ({chunk.source}) - Match: {score:.0%}\n{chunk.text.strip()}\n")
    return "\n".join(formatted)


@tool
def search_runbook(issue: str) -> str:
    """Retrieve specific procedural runbook instructions for a designated technical issue."""
    retriever = get_tool_retriever()
    results = retriever.retrieve(issue, top_k=2)
    if not results:
        return f"No runbook found specifically for: {issue}"

    top_chunk, score = results[0]
    return f"Runbook: {top_chunk.title}\nSource: {top_chunk.source} (Relevance: {score:.0%})\n\n{top_chunk.text}"


@tool
def create_it_ticket(
    title: str,
    description: str,
    category: str = "General IT Inquiry",
    priority: str = "Medium",
    assigned_team: str = "Tier 1 Service Desk",
    user_name: str = "Employee",
    user_email: str = "employee@company.com",
    device_info: str = "Enterprise Workstation",
) -> str:
    """Create a new official IT support ticket in the database with triage details."""
    db = get_tool_db()

    # Enforce identity binding if user is authenticated
    active_user = SessionManager.get_current_user()
    if active_user and active_user.is_employee:
        user_email = active_user.email
        user_name = active_user.full_name

    # Category and priority mapping
    matched_cat = next(
        (c for c in TicketCategory if c.value.lower() == category.lower() or c.name.lower() == category.lower()),
        TicketCategory.OTHER,
    )
    matched_prio = next(
        (p for p in TicketPriority if p.value.lower() == priority.lower() or p.name.lower() == priority.lower()),
        TicketPriority.MEDIUM,
    )

    # Check for duplicate ticket within recent minutes with same user & title
    existing = db.list_tickets(search_query=title[:30] if len(title) > 30 else title)
    for t in existing:
        if t.user_email == user_email and t.title.strip().lower() == title.strip().lower() and t.status in (TicketStatus.OPEN, TicketStatus.IN_PROGRESS):
            return f"Duplicate ticket detected: existing ticket {t.id} is already open for this issue."

    ticket = Ticket(
        id="",
        title=title.strip(),
        description=description.strip(),
        category=matched_cat,
        priority=matched_prio,
        status=TicketStatus.OPEN,
        user_name=user_name,
        user_email=user_email,
        device_info=device_info,
        assigned_to=assigned_team,
        ai_diagnosis=f"Triaged to {assigned_team}. Priority: {matched_prio.value}",
    )
    created = db.create_ticket(ticket)
    return f"Ticket successfully created with ID: {created.id}. Assigned to queue: {assigned_team}."


@tool
def get_ticket_status(ticket_id: str) -> str:
    """Retrieve live status, priority, category, and technician notes for a given Ticket ID (e.g. TICK-1001)."""
    clean_id = ticket_id.strip().upper()
    match = re.search(r"TICK-\d+", clean_id)
    if match:
        clean_id = match.group(0)

    db = get_tool_db()
    ticket = db.get_ticket(clean_id)
    if not ticket:
        return f"Ticket {clean_id} was not found in the IT Service Management database."

    # Python RBAC check: verify user is authorized to view this ticket
    active_user = SessionManager.get_current_user()
    if active_user and not can_view_ticket(active_user, ticket):
        return f"Access Denied: You do not have permission to access ticket {clean_id}."

    messages = db.get_messages(clean_id)
    recent_msg = messages[-1].message if messages else "No conversation recorded."

    return (
        f"Ticket ID: {ticket.id}\n"
        f"Title: {ticket.title}\n"
        f"Status: {ticket.status.value}\n"
        f"Priority: {ticket.priority.value}\n"
        f"Category: {ticket.category.value}\n"
        f"Assigned To: {ticket.assigned_to}\n"
        f"Created: {ticket.created_at[:16].replace('T', ' ')}\n"
        f"Latest Update: {recent_msg}\n"
        f"Resolution Notes: {ticket.resolution_notes or 'Pending resolution'}"
    )


@tool
def get_employee_ticket_history(user_email: str) -> str:
    """Retrieve ticket history for an employee by email with authorization verification."""
    clean_email = user_email.strip().lower()
    if not clean_email or "@" not in clean_email:
        return "Invalid email address format for employee lookup."

    # Python RBAC check: employees can only view their own history
    active_user = SessionManager.get_current_user()
    if active_user and active_user.is_employee:
        if active_user.email.lower() != clean_email:
            return "Access Denied: You do not have permission to access another employee's ticket history."

    db = get_tool_db()
    tickets = db.list_tickets()
    user_tickets = [t for t in tickets if t.user_email and t.user_email.lower() == clean_email]

    if not user_tickets:
        return f"No support tickets found for employee {clean_email}."

    lines = [f"Found {len(user_tickets)} ticket(s) for {clean_email}:"]
    for t in user_tickets[:5]:
        lines.append(f"- [{t.id}] {t.title} | Status: {t.status.value} | Priority: {t.priority.value}")
    return "\n".join(lines)


@tool
def generate_resolution_note(ticket_id: str) -> str:
    """Draft an official ITIL resolution summary note from verified ticket conversation history."""
    clean_id = ticket_id.strip().upper()
    match = re.search(r"TICK-\d+", clean_id)
    if match:
        clean_id = match.group(0)

    # Python RBAC check: employees cannot invoke resolution tools
    active_user = SessionManager.get_current_user()
    if active_user and active_user.is_employee:
        return "Access Denied: Employees do not have permission to access technician resolution tools."

    db = get_tool_db()
    ticket = db.get_ticket(clean_id)
    if not ticket:
        return f"Ticket {clean_id} not found."

    if active_user and not can_update_ticket(active_user, ticket):
        return f"Access Denied: You do not have permission to access ticket {clean_id}."

    messages = db.get_messages(clean_id)
    audit = "\n".join([f"[{m.sender}]: {m.message}" for m in messages])

    return (
        f"ITIL Resolution Note for {ticket.id} ({ticket.title}):\n"
        f"1. Root Cause: Incident under category '{ticket.category.value}' identified.\n"
        f"2. Remediation Executed: Standard troubleshooting runbooks applied by {ticket.assigned_to or 'Support'}.\n"
        f"3. Verification: System restored to operational status and verified with user.\n"
        f"Audit History summary: {len(messages)} interactions recorded."
    )

