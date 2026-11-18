"""Technician and Admin Dashboard for Ticket Management, Triage, and Analytics."""

from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Optional
from src.database.db_manager import DatabaseManager
from src.llm.triage_agent import SupportTriageAgent
from src.models.ticket import TicketStatus, TicketPriority, TicketCategory, TicketMessage
from src.models.user import User
from src.auth.session_manager import SessionManager
from src.auth.permissions import require_role, can_update_ticket, AccessDeniedError


def render_dashboard_view(
    db: DatabaseManager,
    agent: SupportTriageAgent,
    user: Optional[User] = None,
) -> None:
    current_user = user or SessionManager.get_current_user()
    require_role(["technician", "admin"], user=current_user)

    st.subheader("🛠️ Technician Workspace & Incident Management")
    st.caption(
        f"Technician: **{current_user.full_name}** | **Technician ID:** `{current_user.id}` | Team Queue: `{current_user.team or 'All Queues'}`"
    )

    # 1. Summary Metrics KPIs
    stats = db.get_stats()
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)

    m_col1.metric("Total Tickets", stats["total_tickets"])
    m_col2.metric("Open Queue", stats["open_tickets"], delta=f"{stats['open_tickets']} active", delta_color="inverse")
    m_col3.metric("In Progress", stats["in_progress_tickets"])
    m_col4.metric("Resolution Rate", f"{stats['resolution_rate']}%")
    m_col5.metric("Avg Satisfaction", f"{stats['avg_rating']} ⭐")

    st.divider()

    # 2. Charts & Analytics Expander
    with st.expander("📈 Service Desk Analytics & Distribution Charts", expanded=False):
        ch_col1, ch_col2 = st.columns(2)
        with ch_col1:
            st.markdown("**Tickets by Priority**")
            prio_data = stats.get("priority_distribution", {})
            if prio_data:
                df_prio = pd.DataFrame(
                    list(prio_data.items()), columns=["Priority", "Count"]
                ).set_index("Priority")
                st.bar_chart(df_prio)
            else:
                st.write("No priority data yet.")

        with ch_col2:
            st.markdown("**Tickets by Category**")
            cat_data = stats.get("category_distribution", {})
            if cat_data:
                df_cat = pd.DataFrame(
                    list(cat_data.items()), columns=["Category", "Count"]
                ).set_index("Category")
                st.bar_chart(df_cat)
            else:
                st.write("No category data yet.")

    # 3. Filters
    f_col1, f_col2, f_col3, f_col4 = st.columns([2, 2, 2, 3])
    with f_col1:
        status_filter = st.selectbox(
            "Status",
            ["All", "Open", "In Progress", "Waiting on User", "Resolved", "Closed"],
        )
    with f_col2:
        priority_filter = st.selectbox(
            "Priority",
            ["All", "Critical", "High", "Medium", "Low"],
        )
    with f_col3:
        category_options = ["All"] + [c.value for c in TicketCategory]
        category_filter = st.selectbox("Category", category_options)
    with f_col4:
        search_query = st.text_input("🔍 Search Tickets", placeholder="Search title, description, ID...")

    tickets = db.list_tickets_for_user(
        user=current_user,
        status=status_filter if status_filter != "All" else None,
        priority=priority_filter if priority_filter != "All" else None,
        category=category_filter if category_filter != "All" else None,
        search_query=search_query.strip() if search_query.strip() else None,
    )

    st.write(f"Showing **{len(tickets)}** tickets:")

    if not tickets:
        st.info("No tickets found matching the selected filters.")
        return

    # 4. Master Ticket Table & Selection
    ticket_rows = []
    for t in tickets:
        p_badge = {
            TicketPriority.CRITICAL: "🔴 Critical",
            TicketPriority.HIGH: "🟠 High",
            TicketPriority.MEDIUM: "🟡 Medium",
            TicketPriority.LOW: "🟢 Low",
        }.get(t.priority, t.priority.value)

        s_badge = {
            TicketStatus.OPEN: "🔵 Open",
            TicketStatus.IN_PROGRESS: "🔄 In Progress",
            TicketStatus.WAITING_ON_USER: "⏳ Waiting",
            TicketStatus.RESOLVED: "✅ Resolved",
            TicketStatus.CLOSED: "⬛ Closed",
        }.get(t.status, t.status.value)

        ticket_rows.append({
            "ID": t.id,
            "Title": t.title,
            "Category": t.category.value,
            "Priority": p_badge,
            "Status": s_badge,
            "Assignee": t.assigned_to or "Unassigned",
            "User": t.user_name,
            "Created": t.created_at[:16].replace("T", " "),
        })

    df = pd.DataFrame(ticket_rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # 5. Ticket Detail Inspector & Actions
    st.divider()
    st.markdown("#### 🛠️ Ticket Detail & Technician Actions")

    ticket_ids = [t.id for t in tickets]
    selected_id = st.selectbox("Select Ticket to Inspect & Update", ticket_ids)
    selected_ticket = db.get_ticket(selected_id)

    if not selected_ticket:
        return

    t_col1, t_col2 = st.columns([3, 2])

    with t_col1:
        st.markdown(f"### `{selected_ticket.id}`: {selected_ticket.title}")
        st.write(f"**Reported by:** {selected_ticket.user_name} (`{selected_ticket.user_email}`)")
        st.write(f"**Device / OS:** `{selected_ticket.device_info or 'Not specified'}`")
        st.write(f"**Created:** `{selected_ticket.created_at[:19].replace('T', ' ')}`")

        st.markdown("**Original Incident Description:**")
        st.info(selected_ticket.description)

        if selected_ticket.ai_diagnosis:
            st.markdown("**🤖 AI Diagnostic Assessment:**")
            st.success(selected_ticket.ai_diagnosis)

        if selected_ticket.suggested_steps:
            st.markdown("**📋 Recommended Steps:**")
            st.markdown(selected_ticket.suggested_steps)

        # Audit / Message History
        st.markdown("##### 💬 Ticket Conversation & Audit Thread")
        messages = db.get_messages(selected_ticket.id)
        for msg in messages:
            sender_label = {
                "user": f"👤 User ({selected_ticket.user_name})",
                "ai_assistant": "🤖 AI Assistant",
                "technician": f"🛠️ Technician ({selected_ticket.assigned_to})",
                "system": "⚙️ System",
            }.get(msg.sender, msg.sender)

            with st.chat_message("user" if msg.sender == "user" else "assistant"):
                st.caption(f"{sender_label} - `{msg.timestamp[:16].replace('T', ' ')}`")
                st.markdown(msg.message)

        # Add message input
        with st.form(key=f"reply_form_{selected_ticket.id}", clear_on_submit=True):
            reply_text = st.text_area("Add Technician Note / Reply to User", height=80)
            reply_btn = st.form_submit_button("📨 Post Note to Ticket")
            if reply_btn and reply_text.strip():
                db.add_message(
                    TicketMessage(
                        ticket_id=selected_ticket.id,
                        sender="technician",
                        message=reply_text.strip(),
                    )
                )
                st.success("Note added to ticket audit thread!")
                st.rerun()

    with t_col2:
        st.markdown("##### ⚙️ Status & Lifecycle Controls")

        status_options = list(TicketStatus)
        curr_status_idx = (
            status_options.index(selected_ticket.status)
            if selected_ticket.status in status_options
            else 0
        )
        new_status = st.selectbox(
            "Change Status",
            options=status_options,
            format_func=lambda x: x.value,
            index=curr_status_idx,
            key=f"status_select_{selected_ticket.id}",
        )

        assignee_input = st.text_input(
            "Assigned Technician",
            value=selected_ticket.assigned_to or "Dave Miller (NetOps)",
            key=f"assignee_input_{selected_ticket.id}",
        )

        st.markdown("**Resolution Notes:**")
        # AI Draft Resolution Button
        if st.button("✨ AI Draft Resolution Summary", use_container_width=True):
            with st.spinner("Drafting ITIL compliant resolution note..."):
                messages = db.get_messages(selected_ticket.id)
                draft = agent.generate_resolution_summary(selected_ticket, messages)
                st.session_state[f"res_notes_{selected_ticket.id}"] = draft

        current_res_notes = st.session_state.get(
            f"res_notes_{selected_ticket.id}",
            selected_ticket.resolution_notes or "",
        )

        resolution_notes = st.text_area(
            "Resolution Notes (Required to Close)",
            value=current_res_notes,
            height=120,
            key=f"res_textarea_{selected_ticket.id}",
        )

        if st.button("💾 Save Ticket Updates", type="primary", use_container_width=True):
            selected_ticket.status = new_status
            selected_ticket.assigned_to = assignee_input.strip()
            selected_ticket.resolution_notes = resolution_notes.strip() if resolution_notes.strip() else None

            db.update_ticket(selected_ticket)
            db.add_message(
                TicketMessage(
                    ticket_id=selected_ticket.id,
                    sender="system",
                    message=f"Ticket updated by `{assignee_input}`. Status set to `{new_status.value}`.",
                )
            )
            st.success(f"Ticket {selected_ticket.id} successfully updated!")
            st.rerun()

