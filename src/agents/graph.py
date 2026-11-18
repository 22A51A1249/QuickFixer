"""StateGraph Orchestrator for QuickFixer Agentic Workflow."""

from __future__ import annotations

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from src.agents.state import SupportState
from src.agents.nodes import (
    receive_query_node,
    classify_query_node,
    out_of_scope_node,
    retrieve_knowledge_node,
    generate_response_node,
    check_resolution_node,
    ticket_triage_node,
    human_approval_node,
    create_ticket_node,
    route_ticket_node,
    ticket_status_lookup_node,
    resolution_summary_node,
    end_node,
)
from src.agents.routing import (
    route_by_query_intent,
    route_after_resolution_check,
    route_after_approval,
)
from src.agents.checkpointer import get_checkpointer


def build_support_graph(checkpointer=None) -> Any:
    """Construct and compile the 12-node LangGraph StateGraph."""
    workflow = StateGraph(SupportState)

    # Register Nodes
    workflow.add_node("receive_query_node", receive_query_node)
    workflow.add_node("classify_query_node", classify_query_node)
    workflow.add_node("out_of_scope_node", out_of_scope_node)
    workflow.add_node("retrieve_knowledge_node", retrieve_knowledge_node)
    workflow.add_node("generate_response_node", generate_response_node)
    workflow.add_node("check_resolution_node", check_resolution_node)
    workflow.add_node("ticket_triage_node", ticket_triage_node)
    workflow.add_node("human_approval_node", human_approval_node)
    workflow.add_node("create_ticket_node", create_ticket_node)
    workflow.add_node("route_ticket_node", route_ticket_node)
    workflow.add_node("ticket_status_lookup_node", ticket_status_lookup_node)
    workflow.add_node("resolution_summary_node", resolution_summary_node)
    workflow.add_node("end_node", end_node)

    # Edges & Flow
    workflow.add_edge(START, "receive_query_node")
    workflow.add_edge("receive_query_node", "classify_query_node")

    # Conditional routing from classify
    workflow.add_conditional_edges(
        "classify_query_node",
        route_by_query_intent,
        {
            "out_of_scope_node": "out_of_scope_node",
            "retrieve_knowledge_node": "retrieve_knowledge_node",
            "ticket_status_lookup_node": "ticket_status_lookup_node",
            "ticket_triage_node": "ticket_triage_node",
            "create_ticket_node": "create_ticket_node",
        },
    )

    # Out of scope -> End
    workflow.add_edge("out_of_scope_node", "end_node")

    # Retrieval -> Generation -> End
    workflow.add_edge("retrieve_knowledge_node", "generate_response_node")
    workflow.add_edge("generate_response_node", "end_node")

    # Ticket status lookup -> End
    workflow.add_edge("ticket_status_lookup_node", "end_node")

    # Triage -> Routing -> Human Approval
    workflow.add_edge("ticket_triage_node", "route_ticket_node")
    workflow.add_edge("route_ticket_node", "human_approval_node")

    # Conditional approval -> Create ticket or End
    workflow.add_conditional_edges(
        "human_approval_node",
        route_after_approval,
        {
            "create_ticket_node": "create_ticket_node",
            "end_node": "end_node",
        },
    )

    workflow.add_edge("create_ticket_node", "end_node")
    workflow.add_edge("resolution_summary_node", "end_node")
    workflow.add_edge("end_node", END)

    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    return workflow.compile()


# Global compiled graph singleton
_graph = None


def get_compiled_graph():
    global _graph
    if _graph is None:
        checkpointer = get_checkpointer()
        _graph = build_support_graph(checkpointer=checkpointer)
    return _graph


def run_support_agent(
    message: str,
    session_id: str = "default_session",
    thread_id: Optional[str] = None,
    user_name: str = "Employee",
    user_email: str = "employee@company.com",
    approval_status: Optional[str] = None,
    conversation_history: Optional[list] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Execute the LangGraph agent for a user message within a persistent thread."""
    active_thread_id = thread_id or session_id
    graph = get_compiled_graph()
    thread_config = {"configurable": {"thread_id": active_thread_id}}

    initial_state: Dict[str, Any] = {
        "question": message,
        "session_id": active_thread_id,
        "user_id": user_email,
        "user_name": user_name,
        "user_email": user_email,
    }

    if conversation_history:
        initial_state["conversation_history"] = conversation_history

    if approval_status:
        initial_state["approval_status"] = approval_status

    for k, v in kwargs.items():
        if v is not None:
            initial_state[k] = v

    final_state = graph.invoke(initial_state, config=thread_config)
    return final_state
