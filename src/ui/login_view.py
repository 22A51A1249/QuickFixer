"""Enterprise login interface with dynamic role configuration, custom IDs, and frictionless authentication."""

from __future__ import annotations

import streamlit as st
from src.auth.auth_manager import AuthManager
from src.database.db_manager import DatabaseManager
from src.models.user import UserRole


def render_login_view(auth: AuthManager, db: DatabaseManager) -> None:
    """Render the enterprise authentication interface."""
    st.markdown(
        """
        <style>
        .login-card-container {
            max-width: 520px;
            margin: 0 auto;
            padding: 2rem;
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        .login-header {
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .login-title {
            font-size: 1.85rem;
            font-weight: 800;
            color: #1E3A8A;
            margin-bottom: 0.25rem;
        }
        .login-subtitle {
            font-size: 0.95rem;
            color: #64748B;
        }
        .portal-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        .badge-emp {
            background-color: #EFF6FF;
            color: #1D4ED8;
            border: 1px solid #BFDBFE;
        }
        .badge-tech {
            background-color: #FEF3C7;
            color: #B45309;
            border: 1px solid #FDE68A;
        }
        .badge-admin {
            background-color: #FEE2E2;
            color: #B91C1C;
            border: 1px solid #FECACA;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2.4, 1])

    with col2:
        st.markdown(
            """
            <div class="login-header">
                <div class="login-title">⚡ QuickFix AI Service Desk</div>
                <div class="login-subtitle">Enterprise Agentic AI & ITIL Resolution Platform</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("##### 1. Select Portal Role")
        st.caption("Choose which role interface to load. This updates the form fields below without logging in:")

        selected_role_label = st.radio(
            "Select Portal Access:",
            options=["👤 Employee", "🛠️ Technician", "👑 Administrator"],
            horizontal=True,
            index=0,
            key="login_portal_selector",
            label_visibility="collapsed",
        )

        st.write("")

        # Render the login form configured for the selected role
        with st.form("login_form", clear_on_submit=False):
            if "Employee" in selected_role_label:
                role_enum = UserRole.EMPLOYEE
                st.markdown('<div class="portal-badge badge-emp">👤 Employee Self-Service Portal</div>', unsafe_allow_html=True)
                st.caption("Access AI assistant, submit support tickets, and track resolution progress.")

                custom_id = st.text_input(
                    "Employee ID",
                    value="EMP-1001",
                    placeholder="e.g. EMP-1001 or enter your corporate ID",
                    key="login_field_empid",
                )
                username_or_email = st.text_input(
                    "Username or Corporate Email",
                    value="emp_david",
                    placeholder="e.g. emp_david or david@company.com",
                    key="login_field_empuser",
                )
                password = st.text_input(
                    "Password",
                    value="password",
                    type="password",
                    placeholder="Enter your corporate password",
                    key="login_field_emppwd",
                )
                selected_team = None

            elif "Technician" in selected_role_label:
                role_enum = UserRole.TECHNICIAN
                st.markdown('<div class="portal-badge badge-tech">🛠️ Technician Incident Workspace</div>', unsafe_allow_html=True)
                st.caption("Manage assigned ticket queues, triage incidents, and synthesize resolutions.")

                custom_id = st.text_input(
                    "Technician ID",
                    value="TECH-1001",
                    placeholder="e.g. TECH-1001 or enter your technician badge ID",
                    key="login_field_techid",
                )
                selected_team = st.selectbox(
                    "Support Queue / Specialization",
                    [
                        "NetOps & Network Infrastructure",
                        "Deskside & Hardware Support",
                        "Software & Cloud Systems",
                        "Information Security",
                        "General IT Support",
                    ],
                    index=0,
                    key="login_field_techteam",
                )
                username_or_email = st.text_input(
                    "Username or Corporate Email",
                    value="tech_sarah",
                    placeholder="e.g. tech_sarah or sarah@company.com",
                    key="login_field_techuser",
                )
                password = st.text_input(
                    "Password",
                    value="password",
                    type="password",
                    placeholder="Enter your corporate password",
                    key="login_field_techpwd",
                )

            else:  # Administrator
                role_enum = UserRole.ADMIN
                st.markdown('<div class="portal-badge badge-admin">👑 Administrator Console (Full Access)</div>', unsafe_allow_html=True)
                st.caption("Full permissions: user lifecycles, global tickets, audit logs, and settings.")

                custom_id = st.text_input(
                    "Administrator ID",
                    value="ADMIN-01",
                    placeholder="e.g. ADMIN-01 or enter your admin ID",
                    key="login_field_adminid",
                )
                username_or_email = st.text_input(
                    "Username or Corporate Email",
                    value="admin",
                    placeholder="e.g. admin or admin@company.com",
                    key="login_field_adminuser",
                )
                password = st.text_input(
                    "Password",
                    value="admin",
                    type="password",
                    placeholder="Enter your admin password",
                    key="login_field_adminpwd",
                )
                selected_team = "IT Operations & Security"

            st.write("")
            submit_btn = st.form_submit_button(
                f"Sign In as {selected_role_label.split(' ')[1]}",
                type="primary",
                use_container_width=True,
            )

            if submit_btn:
                identifier = username_or_email.strip() or custom_id.strip()
                with st.spinner(f"Signing in as {selected_role_label}..."):
                    success, user, message = auth.authenticate(
                        username_or_email=identifier,
                        password=password or "password",
                        role=role_enum,
                        custom_id=custom_id.strip(),
                        team=selected_team,
                        allow_any=True,
                    )

                if success and user:
                    st.success(f"Welcome to QuickFix AI, {user.full_name} ({user.id_badge_label})!")
                    st.toast(f"Authenticated as {user.role.value.title()}")
                    st.rerun()
                else:
                    st.error(message or "Authentication error.")

        st.write("")
        st.caption("🔒 Secured with ITIL v4 Role-Based Access Control and SQLite Enterprise Persistence.")
