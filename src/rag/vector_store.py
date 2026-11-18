"""LangChain-powered FAISS Vector Store for QuickFixer.

Manages persistent dense semantic retrieval, document chunk indexing,
and similarity search with source attribution.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy
from config.settings import settings
from src.rag.document_loader import DocumentChunk
from src.rag.embeddings import ApexEmbeddings


class FAISSVectorStore:
    """Enterprise Vector Store managing LangChain FAISS index and chunk persistence."""

    def __init__(self, index_dir: Optional[Path] = None, embeddings: Optional[ApexEmbeddings] = None):
        self.index_dir = index_dir or settings.VECTOR_INDEX_DIR
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.index_dir / "chunks.json"

        self.embeddings = embeddings or ApexEmbeddings()
        self.vectorstore: Optional[FAISS] = None
        self.chunks: List[DocumentChunk] = []

        # Attempt to load existing index
        self.load()

    def build_index(self, chunks: List[DocumentChunk]) -> None:
        """Build or rebuild FAISS index from document chunks."""
        self.chunks = chunks
        if not chunks:
            self.vectorstore = None
            return

        # Fit fallback vocabulary on chunks
        texts = [f"{c.title}\n{c.text}" for c in chunks]
        self.embeddings.fit_fallback(texts)

        # Convert to LangChain Document objects with rich metadata
        documents = [
            Document(
                page_content=c.text,
                metadata={
                    "doc_id": c.doc_id,
                    "source": c.source,
                    "title": c.title,
                    "chunk_index": c.chunk_index,
                    "category": getattr(c, "category", "OTHER_IT_SUPPORT"),
                    "subcategory": getattr(c, "subcategory", "GENERAL_IT"),
                    "document_type": getattr(c, "document_type", "troubleshooting_guide"),
                },
            )
            for c in chunks
        ]

        self.vectorstore = FAISS.from_documents(
            documents,
            self.embeddings,
            distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT,
        )
        self.save()

    def build_from_documents(self, documents: List[Document]) -> None:
        """Build FAISS index directly from LangChain Document objects."""
        if not documents:
            self.vectorstore = None
            self.chunks = []
            return

        texts = [d.page_content for d in documents]
        self.embeddings.fit_fallback(texts)

        self.chunks = [
            DocumentChunk.from_lc_document(doc, idx)
            for idx, doc in enumerate(documents)
        ]
        self.vectorstore = FAISS.from_documents(
            documents,
            self.embeddings,
            distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT,
        )
        self.save()

    def add_documents(self, new_chunks: List[DocumentChunk]) -> None:
        """Incrementally append new chunks to existing index."""
        if not new_chunks:
            return

        all_chunks = self.chunks + new_chunks
        self.build_index(all_chunks)

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        category: Optional[str] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        """Perform calibrated hybrid semantic & lexical similarity search with category isolation."""
        if not self.chunks or self.vectorstore is None:
            return []

        if category in ("OUT_OF_SCOPE", "NEEDS_CLARIFICATION"):
            return []

        k = top_k or settings.TOP_K_RETRIEVAL
        k = min(k, len(self.chunks))
        min_thresh = threshold if threshold is not None else 0.45

        try:
            fetch_k = min(len(self.chunks), max(k * 3, 10))
            results_with_scores = self.vectorstore.similarity_search_with_score(query, k=fetch_k)
            retrieved: List[Tuple[DocumentChunk, float]] = []

            # Stopwords to focus lexical overlap on meaningful diagnostic keywords
            stopwords = {
                "the", "is", "at", "which", "on", "and", "a", "an", "in", "to", "for",
                "with", "my", "of", "was", "while", "iam", "i", "am", "who", "what",
                "how", "why", "where", "tell", "me", "some", "any", "problem", "problems",
                "problenm", "problenms", "issue", "issues", "error", "errors", "help",
                "troubleshoot", "troubleshooting", "assist", "assistance", "support"
            }
            raw_q_tokens = re.findall(r"\w+", query.lower())
            q_tokens = set(t for t in raw_q_tokens if t not in stopwords and len(t) > 1)

            for doc, raw_score in results_with_scores:
                cos_sim = float(raw_score)
                dense_sim = max(0.0, min(1.0, cos_sim))

                # Hard filter: if cosine similarity is near-zero or negative, reject
                if cos_sim < 0.15:
                    continue

                # Category isolation: strictly filter cross-category contamination
                doc_cat = doc.metadata.get("category", "")
                if category and category not in ("OTHER_IT_SUPPORT", "OUT_OF_SCOPE", "NEEDS_CLARIFICATION"):
                    if doc_cat and doc_cat != category:
                        continue

                # Lexical token overlap
                chunk_text = (doc.page_content + " " + doc.metadata.get("title", "")).lower()
                c_tokens = set(re.findall(r"\w+", chunk_text))
                overlap_count = len(q_tokens & c_tokens)
                overlap_ratio = overlap_count / max(len(q_tokens), 1)

                # Calibrated hybrid score
                final_score = 0.65 * dense_sim + 0.35 * min(overlap_ratio * 1.5, 1.0)

                # Category alignment boost
                if category and doc_cat == category:
                    final_score = min(1.0, final_score + 0.10)

                if final_score >= min_thresh:
                    chunk = DocumentChunk(
                        doc_id=doc.metadata.get("doc_id", "chunk"),
                        source=doc.metadata.get("source", "unknown"),
                        title=doc.metadata.get("title", ""),
                        text=doc.page_content,
                        chunk_index=doc.metadata.get("chunk_index", 0),
                        category=doc.metadata.get("category", "OTHER_IT_SUPPORT"),
                        subcategory=doc.metadata.get("subcategory", "GENERAL_IT"),
                        document_type=doc.metadata.get("document_type", "troubleshooting_guide"),
                    )
                    retrieved.append((chunk, round(final_score, 3)))

            if not retrieved:
                retrieved = self._fallback_keyword_search(query, k, category=category)

            retrieved.sort(key=lambda x: x[1], reverse=True)
            return retrieved[:k]
        except Exception:
            # Heuristic token match fallback
            return self._fallback_keyword_search(query, k, category=category)

    def _fallback_keyword_search(
        self, query: str, k: int, category: Optional[str] = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """Deterministic keyword match fallback with category isolation."""
        if category in ("OUT_OF_SCOPE", "NEEDS_CLARIFICATION"):
            return []

        stopwords = {
            "the", "is", "at", "which", "on", "and", "a", "an", "in", "to", "for",
            "with", "my", "of", "was", "while", "iam", "i", "am", "who", "what",
            "how", "why", "where", "tell", "me", "some", "any", "problem", "problems",
            "problenm", "problenms", "issue", "issues", "error", "errors", "help",
            "troubleshoot", "troubleshooting", "assist", "assistance", "support"
        }
        raw_tokens = re.findall(r"\w+", query.lower())
        q_tokens = set(t for t in raw_tokens if t not in stopwords and len(t) > 1)
        if not q_tokens:
            return []
        scores = []
        for c in self.chunks:
            chunk_cat = getattr(c, "category", "")
            if category and category not in ("OTHER_IT_SUPPORT", "OUT_OF_SCOPE", "NEEDS_CLARIFICATION"):
                if chunk_cat and chunk_cat != category:
                    continue
            c_tokens = set(re.findall(r"\w+", (c.title + " " + c.text).lower()))
            overlap = len(q_tokens & c_tokens)
            score = overlap / max(len(q_tokens), 1)
            if category and chunk_cat == category:
                score += 0.15
            if score >= 0.45:
                scores.append((c, min(1.0, round(score, 3))))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]

    def save(self) -> None:
        """Persist FAISS index and chunk metadata locally."""
        if self.vectorstore is not None:
            try:
                self.vectorstore.save_local(str(self.index_dir))
            except Exception:
                pass

        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump([c.to_dict() for c in self.chunks], f, indent=2)
        except Exception:
            pass

    def load(self) -> bool:
        """Load persistent FAISS index and chunk metadata."""
        if not self.metadata_file.exists():
            return False

        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                raw_chunks = json.load(f)
            self.chunks = [DocumentChunk.from_dict(d) for d in raw_chunks]

            # Fit fallback embeddings
            texts = [f"{c.title}\n{c.text}" for c in self.chunks]
            self.embeddings.fit_fallback(texts)

            # Try loading saved LangChain FAISS index
            index_faiss_file = self.index_dir / "index.faiss"
            if index_faiss_file.exists():
                try:
                    self.vectorstore = FAISS.load_local(
                        folder_path=str(self.index_dir),
                        embeddings=self.embeddings,
                        allow_dangerous_deserialization=True,
                    )
                    return True
                except Exception:
                    pass

            # Reconstruct from documents if binary format differs
            documents = [
                Document(
                    page_content=c.text,
                    metadata={
                        "doc_id": c.doc_id,
                        "source": c.source,
                        "title": c.title,
                        "chunk_index": c.chunk_index,
                    },
                )
                for c in self.chunks
            ]
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)
            return True
        except Exception:
            return False
