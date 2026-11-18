"""Employee Ticket Portal: View personal tickets, status tracking, and satisfaction feedback."""

from __future__ import annotations

import streamlit as st
from datetime import datetime
from src.database.db_manager import DatabaseManager
from src.models.user import User
from src.models.ticket import TicketStatus, TicketMessage, TicketFeedback
from src.auth.permissions import require_role, can_view_ticket


def render_employee_tickets_view(db: DatabaseManager, user: User) -> None:
    """Render the employee ticket management view strictly scoped to the user's tickets."""
    require_role(["employee", "admin"], user=user)

    st.subheader("📋 My IT Support Tickets")
    st.caption(f"Showing support tickets submitted by **{user.full_name}** | **Employee ID:** `{user.id}` | Email: `{user.email}`")

    # 1. Quick Ticket Status Tracker
    with st.expander("🔎 Quick Ticket Status Lookup", expanded=False):
        t_col1, t_col2 = st.columns([3, 1])
        with t_col1:
            lookup_id = st.text_input("Enter Ticket ID (e.g. TICK-1001)", key="emp_ticket_lookup_input")
        with t_col2:
            st.write("")
            st.write("")
            lookup_btn = st.button("Track Status", use_container_width=True)

        if lookup_btn and lookup_id.strip():
            clean_id = lookup_id.strip().upper()
            found_ticket = db.get_ticket(clean_id)
            if not found_ticket:
                st.warning(f"Ticket `{clean_id}` was not found.")
            elif not can_view_ticket(user, found_ticket):
                st.error("Access Denied: You do not have permission to access this ticket.")
            else:
                st.success(
                    f"**Ticket Found:** `{found_ticket.id}` - **{found_ticket.title}**\n\n"
                    f"- **Status:** `{found_ticket.status.value}` | **Priority:** `{found_ticket.priority.value}`\n"
                    f"- **Assigned Team:** `{found_ticket.assigned_to or 'Tier 1 Service Desk'}`\n"
                    f"- **Resolution Notes:** {found_ticket.resolution_notes or 'Pending technician resolution'}"
                )

    st.divider()

    # 2. Filter & Fetch My Tickets
    f_col1, f_col2, f_col3 = st.columns([2, 2, 3])
    with f_col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Open", "In Progress", "Waiting on User", "Resolved", "Closed"],
            key="emp_status_filter",
        )
    with f_col2:
        priority_filter = st.selectbox(
            "Filter by Priority",
            ["All", "Critical", "High", "Medium", "Low"],
            key="emp_priority_filter",
        )
    with f_col3:
        search_query = st.text_input("🔍 Search My Tickets", key="emp_ticket_search")

    my_tickets = db.list_tickets_for_user(
        user=user,
        status=status_filter if status_filter != "All" else None,
        priority=priority_filter if priority_filter != "All" else None,
        search_query=search_query.strip() if search_query.strip() else None,
    )

    if not my_tickets:
        st.info("You currently have no support tickets matching these filters.")
        return

    st.write(f"Found **{len(my_tickets)}** ticket(s):")

    for ticket in my_tickets:
        prio_badge = {
            "Critical": "🔴",
            "High": "🟠",
            "Medium": "🟡",
            "Low": "🟢",
        }.get(ticket.priority.value, "⚪")

        status_color = {
            TicketStatus.OPEN: "orange",
            TicketStatus.IN_PROGRESS: "blue",
            TicketStatus.WAITING_ON_USER: "violet",
            TicketStatus.RESOLVED: "green",
            TicketStatus.CLOSED: "gray",
        }.get(ticket.status, "gray")

        exp_title = f"{prio_badge} **[{ticket.id}]** {ticket.title} — :{status_color}[{ticket.status.value}]"

        with st.expander(exp_title, expanded=False):
            t_left, t_right = st.columns([3, 2])

            with t_left:
                st.markdown(f"**Issue Description:**\n{ticket.description}")
                if ticket.resolution_notes:
                    st.info(f"**Technician Resolution Notes:**\n{ticket.resolution_notes}")

            with t_right:
                st.write(f"**Category:** `{ticket.category.value}`")
                st.write(f"**Assigned Queue:** `{ticket.assigned_to or 'Tier 1 Service Desk'}`")
                st.write(f"**Submitted On:** `{ticket.created_at[:16].replace('T', ' ')}`")

            st.markdown("---")
            st.markdown("##### 💬 Conversation & Updates")
            messages = db.get_messages(ticket.id)
            if messages:
                for m in messages:
                    is_me = m.sender.lower() in ("employee", user.username.lower(), user.full_name.lower())
                    role_icon = "👤" if is_me else "🛠️"
                    st.markdown(
                        f"**{role_icon} {m.sender.title()}** *({m.timestamp[:16].replace('T', ' ')})*:\n"
                        f"> {m.message}"
                    )
            else:
                st.caption("No messages recorded yet.")

            # Reply to Ticket
            reply_text = st.text_input("Add a message or update to this ticket:", key=f"emp_reply_{ticket.id}")
            if st.button("Send Reply", key=f"emp_btn_reply_{ticket.id}"):
                if reply_text.strip():
                    db.add_message(
                        TicketMessage(
                            ticket_id=ticket.id,
                            sender=user.full_name,
                            message=reply_text.strip(),
                            timestamp=datetime.now().isoformat(),
                        )
                    )
                    st.success("Reply added to ticket thread!")
                    st.rerun()

            # Feedback if resolved
            if ticket.status in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
                st.markdown("---")
                st.markdown("##### ⭐ Service Quality Rating")
                fb_col1, fb_col2 = st.columns([1, 2])
                with fb_col1:
                    stars = st.feedback("stars", key=f"fb_star_{ticket.id}")
                with fb_col2:
                    comments = st.text_input("Feedback comments (optional):", key=f"fb_comm_{ticket.id}")
                    if st.button("Submit Feedback", key=f"fb_sub_{ticket.id}"):
                        if stars is not None:
                            db.add_feedback(
                                TicketFeedback(
                                    ticket_id=ticket.id,
                                    rating=stars + 1,
                                    comments=comments.strip() or None,
                                    created_at=datetime.now().isoformat(),
                                )
                            )
                            st.success("Thank you for your feedback!")
                            st.rerun()

