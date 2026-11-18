"""LangChain-based text splitting for knowledge base documents."""

from __future__ import annotations

from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.settings import settings


class ApexTextSplitter:
    """Wraps LangChain's RecursiveCharacterTextSplitter with enterprise chunking parameters."""

    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, chunk_overlap: int = settings.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
            keep_separator=True,
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split a list of LangChain documents into chunked documents preserving metadata."""
        if not documents:
            return []
        chunks = self.splitter.split_documents(documents)
        # Enrich metadata with chunk index
        for idx, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = idx
        return chunks

    def split_text(self, text: str) -> List[str]:
        """Split raw text into text chunks."""
        if not text.strip():
            return []
        return self.splitter.split_text(text)

