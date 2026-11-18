"""ApexIT - Enterprise AI IT Support and Ticket Resolution System.
Main Streamlit application entry point with Authentication and Role-Based Access Control.
"""

from __future__ import annotations

import streamlit as st
from config import settings
from src.database.db_manager import DatabaseManager
from src.rag.retriever import KnowledgeRetriever
from src.llm.gemini_client import GeminiClient
from src.llm.triage_agent import SupportTriageAgent
from src.models.user import User, UserRole
from src.auth import AuthManager, SessionManager, AccessDeniedError
from src.ui import (
    render_login_view,
    render_chat_view,
    reset_chat_history,
    render_ticket_view,
    render_dashboard_view,
    render_employee_tickets_view,
    render_admin_view,
    render_knowledge_view,
    render_settings_view,
)

# Page configuration
st.set_page_config(
    page_title="QuickFix AI | Enterprise IT Support & Resolution",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom modern enterprise styling
st.markdown(
    """
    <style>
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    
    /* Top title styling */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-title {
        color: #64748B;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    /* Badge container */
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .status-online {
        background-color: #DCFCE7;
        color: #166534;
        border: 1px solid #86EFAC;
    }
    .status-offline {
        background-color: #FEF9C3;
        color: #854D0E;
        border: 1px solid #FDE047;
    }
    .user-badge {
        background-color: #EFF6FF;
        color: #1D4ED8;
        border: 1px solid #BFDBFE;
        border-radius: 8px;
        padding: 8px 12px;
        margin-bottom: 1rem;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_services():
    """Initialize and cache application service singletons in session state."""
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = DatabaseManager()

    if "auth_manager" not in st.session_state:
        st.session_state.auth_manager = AuthManager(db=st.session_state.db_manager)

    if "retriever" not in st.session_state:
        st.session_state.retriever = KnowledgeRetriever()

    if "gemini_client" not in st.session_state:
        st.session_state.gemini_client = GeminiClient()

    if "triage_agent" not in st.session_state:
        st.session_state.triage_agent = SupportTriageAgent(
            retriever=st.session_state.retriever,
            gemini_client=st.session_state.gemini_client,
        )

    return (
        st.session_state.db_manager,
        st.session_state.auth_manager,
        st.session_state.retriever,
        st.session_state.gemini_client,
        st.session_state.triage_agent,
    )


def main():
    db, auth, retriever, gemini, agent = get_services()

    # Authentication Gate: require login before displaying portals
    current_user = SessionManager.get_current_user()
    if not current_user:
        render_login_view(auth=auth, db=db)
        return

    # Sidebar Navigation & Authenticated User Profile
    with st.sidebar:
        st.markdown("### ⚡ **QuickFix AI**")

        # Authenticated user card
        role_label = current_user.role.value.title()
        role_icon = {
            UserRole.ADMIN: "👑",
            UserRole.TECHNICIAN: "🛠️",
            UserRole.EMPLOYEE: "👤",
        }.get(current_user.role, "👤")

        badge_info = f"<br><span style='color: #2563EB; font-weight: 600; font-size: 0.85rem;'>🏷️ {current_user.id_badge_label}</span>"
        team_info = f"<br><small style='color: #64748B;'>Queue: {current_user.team}</small>" if current_user.team else ""
        st.markdown(
            f"""
            <div class="user-badge">
                <strong>{role_icon} {current_user.full_name}</strong><br>
                <span>Role: <strong>{role_label}</strong></span>
                {badge_info}
                {team_info}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🚪 Sign Out", use_container_width=True, help="End session and log out"):
            SessionManager.logout_user()
            st.toast("Signed out successfully.")
            st.rerun()

        st.markdown("---")

        # LLM / RAG Engine status pill
        if gemini.is_configured():
            st.markdown(
                '<div class="status-badge status-online">🟢 Gemini 2.0 • Online</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="status-badge status-online">🟢 QuickFix AI • RAG Engine Active</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Role-Tailored Navigation Options
        if current_user.is_admin:
            nav_options = [
                "👑 Admin Console",
                "🛠️ All Tickets Workspace",
                "💬 AI Support Assistant",
                "🎫 Submit Support Ticket",
                "📋 My Support Tickets",
                "📚 Knowledge Base & RAG",
                "⚙️ Settings & Diagnostics",
            ]
        elif current_user.role == UserRole.TECHNICIAN:
            nav_options = [
                "🛠️ Technician Workspace",
                "💬 AI Support Assistant",
                "📚 Knowledge Base & RAG",
            ]
        else:  # Employee
            nav_options = [
                "💬 AI Support Assistant",
                "🎫 Submit Support Ticket",
                "📋 My Support Tickets",
                "📚 Knowledge Base & RAG",
            ]

        nav_choice = st.radio("Navigation", options=nav_options, index=0)

        if "AI Support Assistant" in nav_choice:
            if st.button("🗑️ New Chat / Clear History", use_container_width=True, help="Clear active conversation and start a new session"):
                reset_chat_history()
                st.toast("Conversation history cleared!")
                st.rerun()

        st.markdown("---")

        # Quick sidebar metrics
        stats = db.get_stats()
        st.markdown("**Service Desk Snapshot:**")
        st.write(f"- 🔴 Open Tickets: `{stats['open_tickets']}`")
        st.write(f"- 🔄 In Progress: `{stats['in_progress_tickets']}`")
        st.write(f"- 📚 Indexed Runbooks: `{len(list(settings.KNOWLEDGE_BASE_DIR.glob('*.*')))}`")

        st.markdown("---")
        st.caption("QuickFix AI v3.0 | ITIL v4 & RBAC Secured")

    # Top Header
    st.markdown('<div class="main-title">QuickFix AI Service Desk Platform</div>', unsafe_allow_html=True)

    # Route navigation view protected with RBAC
    try:
        if nav_choice == "💬 AI Support Assistant":
            render_chat_view(db=db, agent=agent, user=current_user)
        elif nav_choice == "🎫 Submit Support Ticket":
            render_ticket_view(db=db, agent=agent, user=current_user)
        elif nav_choice == "📋 My Support Tickets":
            render_employee_tickets_view(db=db, user=current_user)
        elif nav_choice in ("🛠️ Technician Workspace", "🛠️ All Tickets Workspace"):
            render_dashboard_view(db=db, agent=agent, user=current_user)
        elif nav_choice == "👑 Admin Console":
            render_admin_view(db=db, auth=auth, user=current_user)
        elif nav_choice == "📚 Knowledge Base & RAG":
            render_knowledge_view(retriever=retriever)
        elif nav_choice == "⚙️ Settings & Diagnostics":
            render_settings_view(db=db, gemini_client=gemini)
    except AccessDeniedError as e:
        st.error(str(e))


if __name__ == "__main__":
    main()
 