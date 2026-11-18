"""Settings and Diagnostics View for LLM configuration, API keys, and database controls."""

from __future__ import annotations

import os
import sys
import streamlit as st
from config import settings
from src.database.db_manager import DatabaseManager
from src.llm.gemini_client import GeminiClient


def render_settings_view(db: DatabaseManager, gemini_client: GeminiClient) -> None:
    st.subheader("⚙️ System Settings & AI Configuration")
    st.caption("Configure Google Gemini credentials, model parameters, and database controls.")

    # 1. Gemini API Configuration
    st.markdown("#### 🔑 Google Gemini API Settings")
    st.write(
        "Enter your Google Gemini API key to enable online LLM inference. "
        "Keys can be obtained free of charge from [Google AI Studio](https://aistudio.google.com/)."
    )

    current_key = gemini_client.api_key or ""
    new_key = st.text_input(
        "Google Gemini API Key",
        value=current_key,
        type="password",
        help="Leave blank to use the built-in offline RAG diagnostic engine.",
    )

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        model_options = [
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]
        model_labels = {
            "gemini-2.0-flash": "gemini-2.0-flash ⭐ (Most Advanced & Free: 1,500 req/day)",
            "gemini-1.5-pro": "gemini-1.5-pro 🧠 (Deep Reasoning: 50 req/day free)",
            "gemini-1.5-flash": "gemini-1.5-flash ⚡ (Fast Standard: 1,500 req/day free)",
        }
        current_model = gemini_client.model_name or settings.GEMINI_MODEL
        curr_idx = model_options.index(current_model) if current_model in model_options else 0

        model_name = st.selectbox(
            "Gemini Model (Free Tier Compatible)",
            options=model_options,
            format_func=lambda m: model_labels.get(m, m),
            index=curr_idx,
            help="gemini-2.0-flash is Google's newest and most advanced model with free quota on Google AI Studio.",
        )
    with col_m2:
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=float(settings.GEMINI_TEMPERATURE),
            step=0.05,
        )

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("💾 Apply API Settings", type="primary", use_container_width=True):
            gemini_client.model_name = model_name
            gemini_client.temperature = temperature
            success = gemini_client.update_key(new_key)
            if success:
                st.success("Gemini API key applied and client configured successfully!")
            elif not new_key:
                st.info("Operating in Local RAG Engine mode.")
            else:
                st.warning("Key updated, but client configuration encountered an issue.")
            st.rerun()

    with btn_col2:
        if st.button("🧪 Test Gemini Connection", use_container_width=True):
            if not gemini_client.is_configured():
                st.error("Gemini is not configured. Please enter a valid API key first.")
            else:
                with st.spinner("Calling Gemini API..."):
                    test_response = gemini_client.generate_response(
                        user_message="Respond with 'Gemini API online and operational.'",
                        conversation_history=[],
                        rag_context="Test context",
                    )
                if test_response:
                    st.success(f"Connection test successful! Model response: `{test_response.strip()}`")
                else:
                    st.error("Failed to receive response from Gemini API. Check API key quota or validity.")

    st.divider()

    # 2. Database Maintenance
    st.markdown("#### 🗄️ Database Management")
    db_size = (
        round(settings.SQLITE_DB_PATH.stat().st_size / 1024, 2)
        if settings.SQLITE_DB_PATH.exists()
        else 0
    )
    st.write(f"- **Database Path:** `{settings.SQLITE_DB_PATH}`")
    st.write(f"- **Current File Size:** `{db_size} KB`")

    if st.button("🔄 Reset Demo Tickets", help="Deletes current database and restores original demo tickets"):
        if settings.SQLITE_DB_PATH.exists():
            try:
                os.remove(settings.SQLITE_DB_PATH)
            except Exception:
                pass
        db.init_db()
        st.success("Database reset with initial demo tickets!")
        st.rerun()

    st.divider()

    # 3. Environment & Diagnostics Summary
    st.markdown("#### 🖥️ Environment Diagnostics")
    d_col1, d_col2 = st.columns(2)

    with d_col1:
        st.write(f"**Python Version:** `{sys.version.split()[0]}`")
        st.write(f"**Streamlit Version:** `{st.__version__}`")
        st.write(f"**FAISS Support:** `Enabled (faiss-cpu)`")

    with d_col2:
        st.write(f"**Local Knowledge Engine:** `{'Active' if settings.ENABLE_OFFLINE_DEMO_FALLBACK else 'Disabled'}`")
        st.write(f"**Embedding Model:** `{settings.EMBEDDING_MODEL_NAME}`")
        st.write(f"**Chunk Size:** `{settings.CHUNK_SIZE}` (Overlap: `{settings.CHUNK_OVERLAP}`)")

