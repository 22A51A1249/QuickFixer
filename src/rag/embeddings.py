"""LangChain-compatible Embeddings module for QuickFixer.

Provides official LangChain Embeddings interface using HuggingFace
SentenceTransformers or a deterministic zero-dependency fallback embedder.
"""

from __future__ import annotations

import math
import re
from typing import List, Dict, Optional
import numpy as np
from langchain_core.embeddings import Embeddings
from config.settings import settings


class ApexEmbeddings(Embeddings):
    """LangChain Embeddings implementation supporting HuggingFace and local fallback."""

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME, dim: int = 384):
        self.model_name = model_name
        self.dim = dim
        self._hf_embeddings = None
        self._vocab: Dict[str, int] = {}
        self._idf: Dict[str, float] = {}
        self._projection_matrix: Optional[np.ndarray] = None
        self._try_init_hf_embeddings()

    def _try_init_hf_embeddings(self) -> None:
        """Attempt to load official HuggingFaceEmbeddings if dependencies exist."""
        try:
            import importlib
            st_mod = importlib.util.find_spec("sentence_transformers")
            if st_mod is not None:
                from langchain_community.embeddings import HuggingFaceEmbeddings
                self._hf_embeddings = HuggingFaceEmbeddings(
                    model_name=self.model_name,
                    encode_kwargs={"normalize_embeddings": True},
                )
        except Exception:
            self._hf_embeddings = None

    def fit_fallback(self, texts: List[str]) -> None:
        """Fit vocabulary and IDF statistics on document texts for fallback dense projection."""
        doc_count = len(texts)
        if doc_count == 0:
            return

        df: Dict[str, int] = {}
        token_set_all = set()

        for text in texts:
            tokens = set(self._tokenize(text))
            token_set_all.update(tokens)
            for t in tokens:
                df[t] = df.get(t, 0) + 1

        sorted_terms = sorted(token_set_all, key=lambda t: df.get(t, 0), reverse=True)[:4000]
        self._vocab = {term: idx for idx, term in enumerate(sorted_terms)}
        self._idf = {
            term: math.log((doc_count + 1) / (df.get(term, 0) + 1)) + 1.0
            for term in self._vocab
        }

        vocab_size = max(len(self._vocab), 1)
        rng = np.random.RandomState(42)
        proj = rng.randn(vocab_size, self.dim).astype(np.float32)
        norms = np.linalg.norm(proj, axis=0, keepdims=True)
        norms[norms == 0] = 1.0
        self._projection_matrix = proj / norms

    def _tokenize(self, text: str) -> List[str]:
        """Normalize text and extract unigrams and bigrams."""
        clean = re.sub(r"[^\w\s-]", " ", text.lower())
        words = clean.split()
        tokens = [w for w in words if len(w) > 1]
        bigrams = [f"{words[i]}_{words[i+1]}" for i in range(len(words) - 1)]
        return tokens + bigrams

    def _encode_text_dense(self, text: str) -> List[float]:
        """Compute single normalized dense float vector."""
        vocab_size = len(self._vocab)
        tokens = self._tokenize(text)

        if not tokens or vocab_size == 0 or self._projection_matrix is None:
            vec = np.zeros(self.dim, dtype=np.float32)
            vec[0] = 1.0
            return vec.tolist()

        tf: Dict[str, float] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        total = len(tokens)

        sparse_vec = np.zeros(vocab_size, dtype=np.float32)
        for t, count in tf.items():
            if t in self._vocab:
                idx = self._vocab[t]
                tfidf = (count / total) * self._idf.get(t, 1.0)
                sparse_vec[idx] = tfidf

        vec = np.dot(sparse_vec, self._projection_matrix[:vocab_size, :])
        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec = vec / norm
        else:
            vec = np.zeros(self.dim, dtype=np.float32)
            vec[0] = 1.0

        return [float(x) for x in vec]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents using HuggingFace or dense fallback."""
        if self._hf_embeddings is not None:
            try:
                return self._hf_embeddings.embed_documents(texts)
            except Exception:
                pass

        if self._projection_matrix is None or len(self._vocab) == 0:
            self.fit_fallback(texts)

        return [self._encode_text_dense(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        """Embed a single search query."""
        if self._hf_embeddings is not None:
            try:
                return self._hf_embeddings.embed_query(text)
            except Exception:
                pass

        if self._projection_matrix is None or len(self._vocab) == 0:
            self.fit_fallback([text])

        return self._encode_text_dense(text)

