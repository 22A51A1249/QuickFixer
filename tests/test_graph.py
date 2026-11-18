"""Unit and integration tests for LangGraph 12-node IT Support Agentic Workflow."""

import pytest
from typing import cast
from src.agents.state import SupportState
from src.agents.graph import build_support_graph, run_support_agent, get_compiled_graph
from src.agents.nodes import (
    receive_query_node,
    classify_query_node,
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


def test_build_and_compile_graph():
    """Verify that StateGraph compiles cleanly without dangling edges or schema errors."""
    graph = build_support_graph()
    assert graph is not None
    assert hasattr(graph, "invoke")


def test_node_receive_query():
    """Test initial state population in receive_query_node."""
    state: SupportState = {
        "question": "Cannot connect to company WiFi",
        "user_email": "alice@company.com",
        "user_name": "Alice Smith",
    }
    result = receive_query_node(state)
    assert result["question"] == "Cannot connect to company WiFi"
    assert result["user_email"] == "alice@company.com"
    assert len(result["conversation_history"]) == 1
    assert result["conversation_history"][0]["role"] == "user"


def test_node_classify_query():
    """Test classification of query intents."""
    # Troubleshooting
    s1: SupportState = {"question": "VPN drops every 10 minutes on my laptop"}
    assert classify_query_node(s1)["query_type"] == "troubleshooting"

    # Ticket status
    s2: SupportState = {"question": "What is the status of TICK-1002?"}
    assert classify_query_node(s2)["query_type"] == "ticket_status"

    # Ticket creation
    s3: SupportState = {"question": "Please create a ticket: monitor won't turn on"}
    assert classify_query_node(s3)["query_type"] == "ticket_creation"

    # Security incident
    s4: SupportState = {"question": "Received a suspicious phishing email asking for password"}
    assert classify_query_node(s4)["query_type"] == "security_incident"


def test_node_retrieve_knowledge():
    """Test FAISS retrieval node."""
    state: SupportState = {"question": "AnyConnect VPN timeout 85 percent"}
    result = retrieve_knowledge_node(state)
    assert "retrieved_documents" in result
    assert "retrieval_scores" in result
    assert len(result["retrieved_documents"]) > 0


def test_node_generate_response():
    """Test response generation node with grounded citations."""
    state: SupportState = {
        "question": "How to resolve VPN timeout?",
        "retrieved_documents": [
            {
                "doc_id": "c1",
                "source": "vpn.md",
                "title": "VPN Guide",
                "text": "Flush DNS using ipconfig /flushdns",
                "score": 0.95,
            }
        ],
    }
    result = generate_response_node(state)
    assert "generated_answer" in result
    assert "Did this resolve your issue?" in result["generated_answer"]


def test_node_check_resolution():
    """Test resolution confirmation node."""
    # User confirmed resolved
    s_yes: SupportState = {"question": "Yes, that completely resolved my issue!"}
    r_yes = check_resolution_node(s_yes)
    assert r_yes["resolution_confirmed"] is True
    assert r_yes["ticket_required"] is False

    # User says not resolved
    s_no: SupportState = {"question": "No, it is still broken, please escalate."}
    r_no = check_resolution_node(s_no)
    assert r_no["resolution_confirmed"] is False
    assert r_no["ticket_required"] is True


def test_node_ticket_triage_and_routing():
    """Test ticket triage and routing logic."""
    state: SupportState = {
        "question": "Network printer NYC-4F is offline and paper jammed",
        "conversation_history": [{"role": "user", "content": "Network printer NYC-4F is offline"}],
    }
    triage = ticket_triage_node(state)
    assert "issue_category" in triage
    assert "priority" in triage
    assert triage["approval_status"] == "pending"

    # Test route ticket node
    merged_state = dict(state)
    merged_state.update(triage)
    routed = route_ticket_node(cast(SupportState, merged_state))
    assert "assigned_team" in routed
    assert any(term in routed["assigned_team"] for term in ("Hardware", "Service Desk", "NetOps"))


def test_node_human_approval_and_ticket_creation():
    """Test approval gate and idempotent ticket creation."""
    state: SupportState = {
        "triage_summary": "Printer offline",
        "issue_category": "Hardware & Peripherals",
        "priority": "Medium",
        "assigned_team": "Hardware Support",
        "approval_status": "pending",
        "question": "Printer is broken",
        "user_name": "Bob",
        "user_email": "bob@company.com",
    }

    # Node presents approval prompt when pending
    appr_res = human_approval_node(state)
    assert appr_res["approval_status"] == "pending"
    assert appr_res["interrupted_for_approval"] is True
    assert "Support Ticket Approval Request" in appr_res["generated_answer"]

    # Once approved, create_ticket_node generates ticket ID
    approved_state = dict(state)
    approved_state["approval_status"] = "approved"
    created_res = create_ticket_node(cast(SupportState, approved_state))
    ticket_id = created_res["ticket_id"]
    assert ticket_id.startswith("TICK-")

    # Idempotency check: calling again on same state does not generate a new ticket
    repeat_state = dict(approved_state)
    repeat_state["ticket_id"] = ticket_id
    repeat_res = create_ticket_node(cast(SupportState, repeat_state))
    assert repeat_res["ticket_id"] == ticket_id


def test_node_ticket_status_lookup():
    """Test ticket status lookup node."""
    state: SupportState = {"question": "Check status of TICK-1001"}
    result = ticket_status_lookup_node(state)
    assert "TICK-1001" in result["generated_answer"]
    assert "Ticket Status Report" in result["generated_answer"]


def test_routing_functions():
    """Verify routing edge decisions."""
    # Intent routing
    assert route_by_query_intent({"query_type": "ticket_status"}) == "ticket_status_lookup_node"
    assert route_by_query_intent({"query_type": "ticket_creation"}) == "ticket_triage_node"
    assert route_by_query_intent({"query_type": "security_incident"}) == "ticket_triage_node"
    assert route_by_query_intent({"query_type": "troubleshooting"}) == "retrieve_knowledge_node"
    assert route_by_query_intent({"approval_status": "approved"}) == "create_ticket_node"

    # Resolution routing
    assert route_after_resolution_check({"resolution_confirmed": True}) == "end_node"
    assert route_after_resolution_check({"ticket_required": True}) == "ticket_triage_node"

    # Approval routing
    assert route_after_approval({"approval_status": "approved"}) == "create_ticket_node"
    assert route_after_approval({"approval_status": "pending"}) == "end_node"


def test_end_to_end_agent_execution():
    """Test end-to-end multi-turn conversation and thread checkpointing."""
    import uuid

    thread_id = f"test_thread_{uuid.uuid4().hex[:8]}"

    # Turn 1: Ask troubleshooting query
    res1 = run_support_agent(
        message="My Cisco AnyConnect VPN times out at 85%",
        session_id=thread_id,
    )
    assert res1.get("query_type") == "troubleshooting"
    assert res1.get("generated_answer") is not None
    assert len(res1.get("retrieved_documents", [])) > 0

    # Turn 2: Query ticket status in same thread
    res2 = run_support_agent(
        message="What is the status of TICK-1001?",
        session_id=thread_id,
    )
    assert res2.get("query_type") == "ticket_status"
    assert "TICK-1001" in res2.get("generated_answer", "")

    # Turn 3: Ask to create a ticket -> triggers triage and pending approval
    res3 = run_support_agent(
        message="Please create a ticket: cannot login to Azure portal",
        session_id=thread_id,
    )
    assert res3.get("query_type") == "ticket_creation"
    assert res3.get("approval_status") == "pending"

    # Turn 4: Approve the ticket -> creates ticket
    res4 = run_support_agent(
        message="Yes, please approve and submit ticket",
        session_id=thread_id,
    )
    assert res4.get("approval_status") == "approved"
    assert res4.get("ticket_id") is not None
    assert res4.get("ticket_id").startswith("TICK-")
