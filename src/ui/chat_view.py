"""End-User IT Support Chat View with LangGraph Agentic Orchestration, RAG Citations, and Human-in-the-Loop Approval."""

from __future__ import annotations

import uuid
import streamlit as st
from typing import Dict, Any, List, Optional
from src.database.db_manager import DatabaseManager
from src.llm.triage_agent import SupportTriageAgent
from src.models.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus
from src.models.user import User
from src.auth.session_manager import SessionManager


INITIAL_ASSISTANT_MESSAGE = {
    "role": "assistant",
    "content": (
        "👋 Hello! I am your AI IT Support Assistant powered by LangGraph & Gemini. "
        "Tell me what technical issue you are experiencing (e.g., VPN drops, MFA reset, "
        "Outlook crash, or printer offline), or ask about a ticket status (e.g., *'Check status of TICK-1001'*)."
    ),
    "sources": [],
    "used_gemini": False,
    "query_type": "general_inquiry",
    "approval_status": None,
    "pending_ticket_data": None,
}


def reset_chat_history() -> None:
    """Reset the chat history and initialize a fresh LangGraph persistent thread ID."""
    st.session_state.session_thread_id = f"sess_{uuid.uuid4().hex[:10]}"
    st.session_state.chat_messages = [dict(INITIAL_ASSISTANT_MESSAGE)]
    st.session_state.pending_approval = None


def get_intent_badge(query_type: str) -> str:
    """Format human-readable badge for agent query intent classification."""
    mapping = {
        "troubleshooting": "🔍 Troubleshooting & Runbook RAG",
        "ticket_creation": "🎫 Ticket Creation & Triage",
        "ticket_status": "🔎 Ticket Status Lookup",
        "security_incident": "🚨 Security Incident Escalation",
        "general_inquiry": "💡 General IT Guidance",
        "out_of_scope": "🚫 Non-IT / Out-of-Scope Guardrail",
    }
    return mapping.get(query_type, f"⚙️ {query_type.replace('_', ' ').title()}")


def render_chat_view(
    db: DatabaseManager,
    agent: SupportTriageAgent,
    user: Optional[User] = None,
) -> None:
    current_user = user or SessionManager.get_current_user()
    emp_name = current_user.full_name if current_user else "Employee"
    emp_email = current_user.email if current_user else "employee@company.com"

    # Ensure persistent session thread ID exists
    if "session_thread_id" not in st.session_state:
        st.session_state.session_thread_id = f"sess_{uuid.uuid4().hex[:10]}"

    if "chat_messages" not in st.session_state:
        reset_chat_history()

    # Header with title and Clear Chat action
    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.subheader("⚡ QuickFix AI Assistant (Agentic)")
        badge_str = f" | {current_user.id_badge_label}" if current_user else ""
        st.caption(
            f"Stateful LangGraph Agentic Pipeline | User: **{emp_name}**{badge_str} | Thread ID: `{st.session_state.session_thread_id}`"
        )
    with head_col2:
        st.write("")
        if st.button("🗑️ Clear Chat History", use_container_width=True, help="Reset conversation thread and start fresh"):
            reset_chat_history()
            st.toast("Conversation thread reset!")
            st.rerun()

    # Quick action prompt pills
    st.markdown("**Quick Runbook Shortcuts:**")
    col1, col2, col3, col4 = st.columns(4)
    quick_prompts = [
        ("🌐 VPN Connection Drops", "My Cisco AnyConnect VPN fails to connect and times out at 85%."),
        ("🔑 MFA Authenticator Issue", "I got a new phone and my Microsoft Authenticator MFA push notifications are not arriving."),
        ("✉️ Outlook Crashing", "Outlook crashes with access violation error when I open a shared mailbox."),
        ("🔎 Check Ticket Status", "What is the status of ticket TICK-1001?"),
    ]

    selected_prompt = None
    if col1.button(quick_prompts[0][0], use_container_width=True):
        selected_prompt = quick_prompts[0][1]
    if col2.button(quick_prompts[1][0], use_container_width=True):
        selected_prompt = quick_prompts[1][1]
    if col3.button(quick_prompts[2][0], use_container_width=True):
        selected_prompt = quick_prompts[2][1]
    if col4.button(quick_prompts[3][0], use_container_width=True):
        selected_prompt = quick_prompts[3][1]

    # Display conversation history
    for idx, msg in enumerate(st.session_state.chat_messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            # If message contains RAG sources, display collapsible citations
            if msg.get("sources"):
                with st.expander("📚 Verified Runbook Citations & Knowledge Matches", expanded=False):
                    for src in msg["sources"]:
                        st.markdown(
                            f"- **{src['title']}** (`{src['source']}`) — Match Score: `{src['score']:.0%}`\n"
                            f"  > *\"{src['snippet']}\"*"
                        )

            # Metadata indicators for assistant turns
            if msg["role"] == "assistant" and idx > 0:
                q_type = msg.get("query_type", "troubleshooting")
                used_gemini = msg.get("used_gemini", False)
                engine_badge = "⚡ Google Gemini LLM" if used_gemini else "🛡️ Internal RAG Diagnostic Engine"
                intent_label = get_intent_badge(q_type)

                st.caption(f"Intent: `{intent_label}` | Engine: `{engine_badge}`")

    # If the last message has a pending human approval for ticket creation, render confirmation card
    last_msg = st.session_state.chat_messages[-1] if st.session_state.chat_messages else None
    if last_msg and last_msg.get("approval_status") == "pending":
        st.info("⚠️ **Human-in-the-Loop Approval Required:** Please review the proposed ticket details before submission.")
        appr_col1, appr_col2 = st.columns(2)
        with appr_col1:
            if st.button("✅ Approve & Submit Ticket", type="primary", use_container_width=True):
                with st.spinner("Submitting ticket through LangGraph orchestrator..."):
                    result = agent.answer_query(
                        user_message="Yes, please approve and create this ticket.",
                        session_id=st.session_state.session_thread_id,
                    )
                    st.session_state.chat_messages.append(
                        {
                            "role": "user",
                            "content": "✅ Ticket submission approved by employee.",
                        }
                    )
                    st.session_state.chat_messages.append(
                        {
                            "role": "assistant",
                            "content": result["answer"],
                            "sources": result["sources"],
                            "used_gemini": result["used_gemini"],
                            "query_type": "ticket_creation",
                            "approval_status": "approved",
                            "ticket_id": result.get("ticket_id"),
                        }
                    )
                    st.balloons()
                    st.rerun()

        with appr_col2:
            if st.button("❌ Cancel Ticket Creation", use_container_width=True):
                result = agent.answer_query(
                    user_message="Cancel ticket creation.",
                    session_id=st.session_state.session_thread_id,
                )
                st.session_state.chat_messages.append(
                    {
                        "role": "user",
                        "content": "Ticket creation cancelled.",
                    }
                )
                st.session_state.chat_messages.append(
                    {
                        "role": "assistant",
                        "content": "Ticket creation cancelled. Let me know if there is anything else I can help with!",
                        "sources": [],
                        "used_gemini": False,
                        "query_type": "troubleshooting",
                        "approval_status": "rejected",
                    }
                )
                st.rerun()

    # Resolution confirmation helper buttons
    elif last_msg and last_msg["role"] == "assistant" and "Did this resolve your issue?" in last_msg.get("content", ""):
        st.markdown("**Did this solution solve your problem?**")
        res_col1, res_col2 = st.columns(2)
        with res_col1:
            if st.button("🎉 Yes, Problem Solved!", type="secondary", use_container_width=True):
                selected_prompt = "Yes, problem is completely resolved! Thank you."
        with res_col2:
            if st.button("🎫 No, Escalate to IT Ticket", type="primary", use_container_width=True):
                selected_prompt = "No, the troubleshooting steps did not resolve it. Please open a ticket."

    # Handle input from chat input box or shortcut buttons
    user_input = st.chat_input("Describe your technical issue, error message, or ticket inquiry...")
    prompt_to_process = selected_prompt or user_input

    if prompt_to_process:
        st.session_state.chat_messages.append({"role": "user", "content": prompt_to_process})
        st.rerun()

    # Process pending response if the last message is from user
    if st.session_state.chat_messages and st.session_state.chat_messages[-1]["role"] == "user":
        last_query = st.session_state.chat_messages[-1]["content"]

        with st.spinner("LangGraph Agent analyzing query, runbooks, and state..."):
            history_for_agent = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.chat_messages[:-1]
            ]
            result = agent.answer_query(
                user_message=last_query,
                conversation_history=history_for_agent,
                session_id=st.session_state.session_thread_id,
            )

        st.session_state.chat_messages.append(
            {
                "role": "assistant",
                "content": result["answer"],
                "sources": result["sources"],
                "used_gemini": result["used_gemini"],
                "query_type": result.get("query_type", "troubleshooting"),
                "approval_status": result.get("approval_status"),
                "ticket_id": result.get("ticket_id"),
            }
        )
        st.rerun()

    # Escalation & Feedback drawer at the bottom of chat
    if len(st.session_state.chat_messages) > 2:
        st.divider()
        st.subheader("Manual Escalation & User Satisfaction")
        esc_col1, esc_col2 = st.columns([2, 1])

        with esc_col1:
            st.write(
                "Need a direct ticket created without further automated troubleshooting? "
                "You can initiate formal ticket triage with full conversation history preserved."
            )
            action_btn1, action_btn2 = st.columns(2)
            with action_btn1:
                if st.button("🎫 Direct IT Ticket Escalation", type="primary", use_container_width=True):
                    user_msgs = [m["content"] for m in st.session_state.chat_messages if m["role"] == "user"]
                    combined_desc = "\n\n".join(user_msgs)
                    triage = agent.triage_ticket(combined_desc)

                    new_ticket = Ticket(
                        id="",
                        title=f"Chat Incident: {triage.summary}",
                        description=combined_desc,
                        category=triage.category,
                        priority=triage.priority,
                        status=TicketStatus.OPEN,
                        user_name=emp_name,
                        user_email=emp_email,
                        assigned_to=triage.recommended_team,
                        ai_diagnosis=f"Triage Team: {triage.recommended_team}. Confidence: {triage.confidence:.0%}",
                        suggested_steps="\n".join([f"- {a}" for a in triage.immediate_actions]),
                    )
                    created = db.create_ticket(new_ticket)
                    st.success(f"Ticket **{created.id}** created successfully! Assigned to queue: `{triage.recommended_team}`.")
                    st.balloons()

            with action_btn2:
                if st.button("🗑️ Reset Chat History", use_container_width=True, help="Clear this conversation and start fresh"):
                    reset_chat_history()
                    st.toast("Conversation thread reset!")
                    st.rerun()

        with esc_col2:
            st.write("Rate this AI Assistant experience:")
            rating = st.feedback("stars", key="csat_rating_stars")
            if rating is not None:
                st.toast(f"Thank you for rating {rating + 1}/5 stars! Your feedback continuously tunes our LangGraph workflows.")
