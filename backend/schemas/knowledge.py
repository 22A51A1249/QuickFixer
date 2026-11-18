"""Knowledge base schemas."""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class DocumentItem(BaseModel):
    filename: str
    size_bytes: int
    modified_at: str
    extension: str


class SearchResultChunk(BaseModel):
    chunk_id: str
    source: str
    title: str
    score: float
    snippet: str
    text: str


class KnowledgeSearchRequest(BaseModel):
    query: str
    top_k: int = 3


class ReindexResponse(BaseModel):
    success: bool
    chunks_indexed: int
    total_files: int
    message: str

