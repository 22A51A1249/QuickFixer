"""Conditional routing functions for the LangGraph StateGraph workflow."""

from __future__ import annotations

from src.agents.state import SupportState


def route_by_query_intent(state: SupportState) -> str:
    """Route initial query based on classified intent."""
    if state.get("approval_status") == "approved" and not state.get("ticket_id"):
        return "create_ticket_node"

    query_type = state.get("query_type", "troubleshooting")
    is_out_of_scope = bool(state.get("is_out_of_scope"))

    if is_out_of_scope or query_type in ("out_of_scope", "clarification_needed"):
        return "out_of_scope_node"

    if query_type == "ticket_status":
        return "ticket_status_lookup_node"
    elif query_type in ("ticket_creation", "security_incident"):
        return "ticket_triage_node"
    else:
        return "retrieve_knowledge_node"


def route_after_resolution_check(state: SupportState) -> str:
    """Route after checking if user issue is resolved."""
    if state.get("resolution_confirmed") is True:
        return "end_node"
    elif state.get("ticket_required") is True:
        return "ticket_triage_node"
    return "end_node"


def route_after_approval(state: SupportState) -> str:
    """Route after human approval check: create ticket if approved, else end."""
    if state.get("approval_status") == "approved":
        return "create_ticket_node"
    return "end_node"
