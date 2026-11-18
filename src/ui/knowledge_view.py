"""Knowledge Base View for Managing IT Runbooks, Vector Indexing, and Semantic Search."""

from __future__ import annotations

import os
import streamlit as st
from pathlib import Path
from config import settings
from src.rag.retriever import KnowledgeRetriever
from src.rag.document_loader import DocumentChunk


def render_knowledge_view(retriever: KnowledgeRetriever) -> None:
    st.subheader("📚 IT Knowledge Base & Vector Index Hub")
    st.caption("Manage standard operating procedures (SOPs), runbooks, and inspect FAISS vector embeddings.")

    # 1. Vector Store Status Metrics
    kb_files = [f for f in settings.KNOWLEDGE_BASE_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]
    total_chunks = len(retriever.vector_store.chunks)

    col1, col2, col3 = st.columns(3)
    col1.metric("Indexed Runbook Files", len(kb_files))
    col2.metric("Total Vector Chunks", total_chunks)
    col3.metric("Vector Store Type", "FAISS IndexFlatIP (Cosine)")

    # 2. Re-indexing & Upload Drawer
    with st.expander("📥 Add New Runbook / Re-index Knowledge Base", expanded=False):
        up_col1, up_col2 = st.columns([2, 1])

        with up_col1:
            uploaded_file = st.file_uploader(
                "Upload Runbook Document (.md, .txt, .pdf, .docx)",
                type=["md", "txt", "pdf", "docx"],
            )
            if uploaded_file is not None:
                save_path = settings.KNOWLEDGE_BASE_DIR / uploaded_file.name
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"File `{uploaded_file.name}` saved to knowledge base directory!")

        with up_col2:
            st.write("Trigger Full Re-indexing:")
            if st.button("🔄 Rebuild FAISS Vector Index", type="primary", use_container_width=True):
                with st.spinner("Parsing documents, splitting chunks, and computing embeddings..."):
                    chunk_count = retriever.reindex_all()
                st.success(f"Successfully re-indexed {chunk_count} chunks into FAISS!")
                st.rerun()

    st.divider()

    # 3. Interactive Vector Search Playground
    st.markdown("#### 🔍 Semantic Retrieval Playground")
    st.write("Test how the FAISS vector store retrieves and ranks chunks for a given IT query:")

    test_col1, test_col2 = st.columns([4, 1])
    with test_col1:
        test_query = st.text_input(
            "Enter IT query to test retrieval",
            value="AnyConnect VPN connection timed out at 85%",
        )
    with test_col2:
        top_k_select = st.number_input("Top K", min_value=1, max_value=8, value=3)

    if test_query.strip():
        results = retriever.retrieve(test_query, top_k=int(top_k_select))
        if results:
            for idx, (chunk, score) in enumerate(results, start=1):
                with st.expander(f"Result #{idx}: {chunk.title} ({chunk.source}) — Score: `{score:.0%}`", expanded=(idx == 1)):
                    st.markdown(f"**Chunk ID:** `{chunk.doc_id}` | **Source File:** `{chunk.source}`")
                    st.markdown(chunk.text)
        else:
            st.warning("No chunks matched with sufficient similarity score.")

    st.divider()

    # 4. Browse Loaded Knowledge Base Runbooks
    st.markdown("#### 📖 Browse Internal Runbooks & Articles")
    if kb_files:
        selected_file_name = st.selectbox("Select Runbook Article", [f.name for f in kb_files])
        selected_file_path = settings.KNOWLEDGE_BASE_DIR / selected_file_name

        try:
            with open(selected_file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            st.markdown(content)
        except Exception as e:
            st.error(f"Error reading file: {e}")
    else:
        st.info("No documents currently found in the knowledge base directory.")

