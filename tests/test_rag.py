"""Unit tests for Document Loading, Chunking, and FAISS Vector Retrieval."""

from pathlib import Path
from src.rag.document_loader import DocumentLoader, DocumentChunk
from src.rag.vector_store import FAISSVectorStore


def test_document_loader_chunking():
    loader = DocumentLoader(chunk_size=200, chunk_overlap=30)
    sample_text = (
        "Cisco AnyConnect connection fails at 85% due to MTU size issues.\n\n"
        "To resolve, open cmd and run ipconfig /flushdns to refresh DNS cache.\n\n"
        "Next, uncheck IPv6 on the network adapter properties dialog."
    )
    chunks = loader.chunk_text(sample_text, source_name="vpn.md", title="VPN Guide")
    assert len(chunks) >= 1
    assert all(isinstance(c, DocumentChunk) for c in chunks)
    assert chunks[0].title == "VPN Guide"


def test_vector_store_indexing_and_search(tmp_path: Path):
    store = FAISSVectorStore(index_dir=tmp_path)

    chunks = [
        DocumentChunk(
            doc_id="chunk_1",
            source="vpn.md",
            title="VPN Troubleshoot",
            text="Cisco AnyConnect VPN connection gateway timed out at 85 percent.",
            chunk_index=0,
        ),
        DocumentChunk(
            doc_id="chunk_2",
            source="printer.md",
            title="Printer Offline",
            text="Office network printer NYC-4F offline print spooler queue stuck.",
            chunk_index=1,
        ),
        DocumentChunk(
            doc_id="chunk_3",
            source="password.md",
            title="Password Policy",
            text="SSPR self-service password reset and Okta authenticator MFA setup.",
            chunk_index=2,
        ),
    ]

    store.build_index(chunks)
    assert len(store.chunks) == 3

    # Query for VPN
    results = store.search("AnyConnect gateway timeout", top_k=2)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert "VPN" in top_chunk.title or "AnyConnect" in top_chunk.text

    # Query for Printer
    p_results = store.search("printer spooler stuck", top_k=2)
    assert len(p_results) > 0
    top_p_chunk, _ = p_results[0]
    assert "printer" in top_p_chunk.text.lower()

