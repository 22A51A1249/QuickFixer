"""LangChain-compatible Knowledge Retriever coordinating FAISS search and context assembly."""

from __future__ import annotations

from typing import List, Tuple, Optional
from config.settings import settings
from src.rag.document_loader import DocumentLoader, DocumentChunk
from src.rag.vector_store import FAISSVectorStore


class KnowledgeRetriever:
    """Orchestrates document indexing, similarity search, and context assembly for RAG."""

    def __init__(self, vector_store: Optional[FAISSVectorStore] = None):
        self.loader = DocumentLoader()
        self.vector_store = vector_store or FAISSVectorStore()
        self.ensure_initialized()

    def ensure_initialized(self) -> None:
        """Check if vector index exists; if not, automatically load knowledge base and index."""
        if not self.vector_store.chunks or self.vector_store.vectorstore is None:
            self.reindex_all()

    def reindex_all(self) -> int:
        """Scan knowledge base directory, generate chunks, and rebuild FAISS index."""
        chunks = self.loader.load_directory()
        if chunks:
            self.vector_store.build_index(chunks)
        return len(chunks)

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        category: Optional[str] = None,
        threshold: Optional[float] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        """Retrieve most relevant knowledge snippets with category filtering and thresholding."""
        self.ensure_initialized()
        return self.vector_store.search(
            query=query,
            top_k=top_k,
            category=category,
            threshold=threshold,
        )

    def as_langchain_retriever(self, top_k: Optional[int] = None):
        """Return native LangChain BaseRetriever."""
        self.ensure_initialized()
        k = top_k or settings.TOP_K_RETRIEVAL
        if self.vector_store.vectorstore is not None:
            return self.vector_store.vectorstore.as_retriever(search_kwargs={"k": k})
        return None

    def format_context(self, results: List[Tuple[DocumentChunk, float]]) -> str:
        """Convert retrieved chunks into a clean, markdown-formatted context block for prompts."""
        if not results:
            return "No specific internal IT runbooks found matching this issue."

        blocks = []
        for idx, (chunk, score) in enumerate(results, start=1):
            source_tag = f"[{chunk.source} - {chunk.title}]"
            relevance = f"(relevance score: {score:.2f})"
            blocks.append(f"--- Document Source {idx}: {source_tag} {relevance} ---\n{chunk.text.strip()}\n")

        return "\n".join(blocks)
