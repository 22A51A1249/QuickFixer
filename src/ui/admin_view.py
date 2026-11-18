"""Administrator Dashboard for User Management, Ticket Reassignment, and Security Audit Logs."""

from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Optional
from src.database.db_manager import DatabaseManager
from src.models.user import User, UserRole, AuditLogEntry
from src.auth.auth_manager import AuthManager
from src.auth.session_manager import SessionManager
from src.auth.permissions import require_role


def render_admin_view(
    db: DatabaseManager,
    auth: AuthManager,
    user: Optional[User] = None,
) -> None:
    """Render the central administrator dashboard."""
    current_user = user or SessionManager.get_current_user()
    require_role(["admin"], user=current_user)

    st.subheader("👑 QuickFix AI Central Administrator Console")
    st.caption("Manage user lifecycles, global ticket assignments, security audit logs, and system operations.")

    # 1. High-Level KPIs
    all_users = db.list_users()
    all_tickets = db.list_tickets()
    stats = db.get_stats()
    audit_logs = db.list_audit_logs(limit=10)

    emp_count = sum(1 for u in all_users if u.role == UserRole.EMPLOYEE)
    tech_count = sum(1 for u in all_users if u.role == UserRole.TECHNICIAN)
    admin_count = sum(1 for u in all_users if u.role == UserRole.ADMIN)

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Total Users", len(all_users), delta=f"{emp_count} Emp / {tech_count} Tech")
    kpi2.metric("Total Tickets", stats["total_tickets"])
    kpi3.metric("Open Incidents", stats["open_tickets"], delta_color="inverse")
    kpi4.metric("Resolution Rate", f"{stats['resolution_rate']}%")
    kpi5.metric("Audit Events", len(db.list_audit_logs(limit=1000)))

    st.divider()

    # Tabs for Admin Operations
    tab_users, tab_tickets, tab_audit = st.tabs([
        "👥 User Lifecycle & Roles",
        "🎫 Ticket Reassignment & Oversight",
        "📜 Security Audit Logs",
    ])

    # -------------------------------------------------------------------------
    # TAB 1: USER MANAGEMENT
    # -------------------------------------------------------------------------
    with tab_users:
        st.markdown("### 👥 Enterprise User Directory")

        # Create New User Expander
        with st.expander("➕ Create New User Account", expanded=False):
            with st.form("admin_create_user_form"):
                u_col1, u_col2 = st.columns(2)
                with u_col1:
                    new_username = st.text_input("Username *", placeholder="e.g. jsmith")
                    new_email = st.text_input("Corporate Email *", placeholder="jsmith@company.com")
                    new_fullname = st.text_input("Full Name *", placeholder="John Smith")
                with u_col2:
                    new_password = st.text_input("Initial Password *", type="password", placeholder="At least 8 chars with letter & digit")
                    new_role = st.selectbox(
                        "User Role *",
                        options=[UserRole.EMPLOYEE, UserRole.TECHNICIAN, UserRole.ADMIN],
                        format_func=lambda r: r.value.title(),
                    )
                    new_team = st.selectbox(
                        "Designated Support Team (Technicians)",
                        options=[
                            "General Service Desk",
                            "NetOps & Network Infrastructure",
                            "Deskside & Hardware Support",
                            "Identity & Access Management (IAM)",
                            "Security Operations Center (SOC)",
                            "Messaging & Collaboration",
                        ],
                    )

                create_user_submit = st.form_submit_button("Create Account", type="primary", use_container_width=True)

                if create_user_submit:
                    if not new_username.strip() or not new_email.strip() or not new_password:
                        st.error("Please fill in all required fields.")
                    else:
                        success, created_usr, msg = auth.create_user(
                            username=new_username,
                            email=new_email,
                            full_name=new_fullname,
                            password=new_password,
                            role=new_role,
                            team=new_team if new_role == UserRole.TECHNICIAN else None,
                            created_by=current_user,
                        )
                        if success:
                            st.success(f"User **{new_username}** created successfully as `{new_role.value}`!")
                            st.rerun()
                        else:
                            st.error(msg)

        # User List & Actions
        st.markdown("##### 📋 Registered Users & Access Control")
        user_rows = []
        for u in all_users:
            status_str = "🟢 Active" if u.is_active else "🔴 Deactivated"
            user_rows.append({
                "User ID": u.id,
                "Username": u.username,
                "Full Name": u.full_name,
                "Email": u.email,
                "Role": u.role.value.title(),
                "Team": u.team or "—",
                "Status": status_str,
                "Created": u.created_at[:10],
            })

        df_users = pd.DataFrame(user_rows)
        st.dataframe(df_users, use_container_width=True)

        st.markdown("##### ⚙️ Manage Selected User Account")
        selected_user_id = st.selectbox(
            "Select User to Modify",
            options=[u.id for u in all_users],
            format_func=lambda uid: f"{uid} — {next((u.full_name for u in all_users if u.id == uid), '')} ({next((u.username for u in all_users if u.id == uid), '')})",
        )

        target_user = next((u for u in all_users if u.id == selected_user_id), None)
        if target_user:
            m_col1, m_col2, m_col3 = st.columns([2, 2, 2])

            with m_col1:
                # Activation toggle
                new_status = not target_user.is_active
                toggle_btn_label = "✅ Activate Account" if not target_user.is_active else "🛑 Deactivate Account"
                if target_user.id == current_user.id:
                    st.button("Cannot Deactivate Self", disabled=True, use_container_width=True)
                else:
                    if st.button(toggle_btn_label, use_container_width=True):
                        auth.update_user_status(target_user.id, new_status, performed_by=current_user)
                        st.success(f"Updated status for {target_user.username} to {'Active' if new_status else 'Deactivated'}.")
                        st.rerun()

            with m_col2:
                # Change role
                role_opts = [UserRole.EMPLOYEE, UserRole.TECHNICIAN, UserRole.ADMIN]
                curr_role_idx = role_opts.index(target_user.role) if target_user.role in role_opts else 0
                selected_new_role = st.selectbox(
                    "Change Role",
                    options=role_opts,
                    format_func=lambda r: r.value.title(),
                    index=curr_role_idx,
                    key=f"role_sel_{target_user.id}",
                )

            with m_col3:
                # Reassign team
                team_opts = [
                    "General Service Desk",
                    "NetOps & Network Infrastructure",
                    "Deskside & Hardware Support",
                    "Identity & Access Management (IAM)",
                    "Security Operations Center (SOC)",
                    "Messaging & Collaboration",
                ]
                selected_new_team = st.selectbox(
                    "Reassign Team",
                    options=team_opts,
                    key=f"team_sel_{target_user.id}",
                )

                if st.button("Apply Role & Team", use_container_width=True):
                    auth.update_user_role(
                        user_id=target_user.id,
                        new_role=selected_new_role,
                        team=selected_new_team if selected_new_role == UserRole.TECHNICIAN else None,
                        performed_by=current_user,
                    )
                    st.success(f"Role and team updated for {target_user.username}!")
                    st.rerun()

    # -------------------------------------------------------------------------
    # TAB 2: TICKET ASSIGNMENT & OVERSIGHT
    # -------------------------------------------------------------------------
    with tab_tickets:
        st.markdown("### 🎫 Global Ticket Oversight & Assignment")
        st.caption("Administrators have full visibility across all departmental queues and can reassign incidents.")

        for t in all_tickets:
            with st.expander(f"**[{t.id}]** {t.title} | Status: `{t.status.value}` | Priority: `{t.priority.value}` | Assigned: `{t.assigned_to or 'Unassigned'}`"):
                st.write(f"**Requester:** {t.user_name} (`{t.user_email}`)")
                st.write(f"**Description:** {t.description}")
                if t.resolution_notes:
                    st.info(f"**Resolution Notes:** {t.resolution_notes}")

                # Reassignment controls
                ass_col1, ass_col2 = st.columns([3, 1])
                with ass_col1:
                    reassign_target = st.selectbox(
                        "Reassign Queue or Technician",
                        options=[
                            "NetOps & Network Infrastructure",
                            "Deskside & Hardware Support",
                            "Identity & Access Management (IAM)",
                            "Security Operations Center (SOC)",
                            "Messaging & Collaboration",
                            "Sarah Connor (Technician)",
                            "Mike Ross (Technician)",
                            "Tier 1 Service Desk",
                        ],
                        key=f"reassign_{t.id}",
                    )
                with ass_col2:
                    st.write("")
                    st.write("")
                    if st.button("Update Assignment", key=f"reassign_btn_{t.id}", use_container_width=True):
                        db.assign_ticket(t.id, reassign_target)
                        db.add_audit_log(
                            AuditLogEntry(
                                user_id=current_user.id,
                                username=current_user.username,
                                action="TICKET_REASSIGNED",
                                resource_type="ticket",
                                resource_id=t.id,
                                details=f"Reassigned ticket {t.id} to '{reassign_target}'.",
                                timestamp=datetime.now().isoformat(),
                            )
                        )
                        st.success(f"Ticket {t.id} reassigned to `{reassign_target}`!")
                        st.rerun()

    # -------------------------------------------------------------------------
    # TAB 3: AUDIT LOGS
    # -------------------------------------------------------------------------
    with tab_audit:
        st.markdown("### 📜 Immutable Security Audit Trail")
        st.caption("Tamper-evident logs of logins, role updates, ticket reassignments, and security incidents.")

        all_logs = db.list_audit_logs(limit=200)

        if all_logs:
            log_rows = []
            for l in all_logs:
                log_rows.append({
                    "Timestamp": l.timestamp[:19].replace("T", " "),
                    "User": l.username or "system",
                    "Action": l.action,
                    "Resource": f"{l.resource_type or ''} {l.resource_id or ''}".strip() or "—",
                    "Details": l.details or "",
                    "IP Address": l.ip_address or "127.0.0.1",
                })
            df_logs = pd.DataFrame(log_rows)
            st.dataframe(df_logs, use_container_width=True)
        else:
            st.info("No security audit events recorded yet.")

