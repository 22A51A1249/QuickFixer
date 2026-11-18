"""Ticket Submission View with Live AI Triage, Entity Extraction, and Priority Prediction."""

from __future__ import annotations

import streamlit as st
from typing import Optional
from src.database.db_manager import DatabaseManager
from src.llm.triage_agent import SupportTriageAgent
from src.models.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus
from src.models.user import User
from src.auth.session_manager import SessionManager


def render_ticket_view(
    db: DatabaseManager,
    agent: SupportTriageAgent,
    user: Optional[User] = None,
) -> None:
    current_user = user or SessionManager.get_current_user()
    default_name = current_user.full_name if current_user else "David Miller"
    default_email = current_user.email if current_user else "dmiller@company.com"

    st.subheader("🎫 Submit New Support Ticket")
    badge_label = f" | {current_user.id_badge_label}" if current_user else ""
    st.caption(f"Report an incident or service request with real-time AI triage and priority scoring.{badge_label}")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("##### 📝 Issue Details")
        title = st.text_input(
            "Incident Title / Brief Summary *",
            placeholder="e.g. Cisco AnyConnect VPN fails to connect with gateway timeout",
        )
        description = st.text_area(
            "Detailed Description & Error Messages *",
            height=160,
            placeholder="Describe what happened, error numbers, steps to reproduce, and impact on your work...",
        )

        user_name = st.text_input("Your Full Name", value=default_name, disabled=bool(current_user and current_user.is_employee))
        user_email = st.text_input("Corporate Email", value=default_email, disabled=bool(current_user and current_user.is_employee))
        device_info = st.selectbox(
            "Device / Operating System",
            [
                "Windows 11 Enterprise (Corporate Laptop)",
                "Windows 10 Pro (Desktop Workstation)",
                "macOS Sonoma (MacBook Pro)",
                "Ubuntu 22.04 LTS (Engineering VM)",
                "iOS / Android Mobile Device",
            ],
        )

    # Real-time AI Triage Analysis Panel in right column
    with col_right:
        st.markdown("##### ⚡ AI Triage & Classification Engine")

        triage_result = None
        if description.strip():
            with st.spinner("Analyzing issue semantics & urgency..."):
                triage_result = agent.triage_ticket(description)

        if triage_result:
            # Color code priorities
            priority_colors = {
                TicketPriority.CRITICAL: "🔴",
                TicketPriority.HIGH: "🟠",
                TicketPriority.MEDIUM: "🟡",
                TicketPriority.LOW: "🟢",
            }
            p_badge = priority_colors.get(triage_result.priority, "⚪")

            st.info(
                f"**Predicted Category:** `{triage_result.category.value}`\n\n"
                f"**Suggested Priority:** {p_badge} **{triage_result.priority.value}**\n\n"
                f"**Confidence Score:** `{triage_result.confidence:.0%}`\n\n"
                f"**Assigned Routing Queue:** `{triage_result.recommended_team}`"
            )

            if triage_result.key_entities:
                st.markdown("**Detected System Entities:**")
                st.write(", ".join([f"`{e}`" for e in triage_result.key_entities]))

            if triage_result.immediate_actions:
                st.markdown("**AI Suggested Initial Remediation:**")
                for action in triage_result.immediate_actions:
                    st.markdown(f"- {action}")
        else:
            st.info("Enter an issue description on the left to see instant AI categorization, priority assignment, and triage recommendations.")

    # Override & Submission controls
    st.divider()
    st.markdown("##### ⚙️ Review Classification & Confirm")
    rev_col1, rev_col2, rev_col3 = st.columns(3)

    default_cat_idx = 0
    default_prio_idx = 2
    if triage_result:
        cats = list(TicketCategory)
        if triage_result.category in cats:
            default_cat_idx = cats.index(triage_result.category)
        prios = list(TicketPriority)
        if triage_result.priority in prios:
            default_prio_idx = prios.index(triage_result.priority)

    with rev_col1:
        selected_category = st.selectbox(
            "Category (AI Suggested)",
            options=list(TicketCategory),
            format_func=lambda x: x.value,
            index=default_cat_idx,
        )

    with rev_col2:
        selected_priority = st.selectbox(
            "Priority (AI Suggested)",
            options=list(TicketPriority),
            format_func=lambda x: x.value,
            index=default_prio_idx,
        )

    with rev_col3:
        st.write("")
        st.write("")
        submit_btn = st.button("🚀 Create Ticket", type="primary", use_container_width=True)

    if submit_btn:
        if not title.strip() or not description.strip():
            st.error("Please provide both an incident title and description before submitting.")
            return

        ai_diag = (
            f"Triage Team: {triage_result.recommended_team}. Confidence: {triage_result.confidence:.0%}"
            if triage_result
            else "Standard ticket intake"
        )
        ai_steps = (
            "\n".join([f"- {a}" for a in triage_result.immediate_actions])
            if triage_result and triage_result.immediate_actions
            else "Awaiting technician assignment"
        )

        ticket = Ticket(
            id="",
            title=title.strip(),
            description=description.strip(),
            category=selected_category,
            priority=selected_priority,
            status=TicketStatus.OPEN,
            user_name=user_name.strip() or "Employee",
            user_email=user_email.strip() or "user@company.com",
            device_info=device_info,
            ai_diagnosis=ai_diag,
            suggested_steps=ai_steps,
        )

        created_ticket = db.create_ticket(ticket)
        st.success(f"🎉 Ticket **{created_ticket.id}** submitted successfully!")
        st.markdown(
            f"- **Title:** {created_ticket.title}\n"
            f"- **Status:** `{created_ticket.status.value}`\n"
            f"- **Priority:** `{created_ticket.priority.value}`\n"
            f"- **Queue:** `{triage_result.recommended_team if triage_result else 'Tier 1 Service Desk'}`"
        )

