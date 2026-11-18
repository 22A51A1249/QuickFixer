"""Knowledge Base & FAISS Vector Index Management Endpoints."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query

from config import settings
from src.rag.retriever import KnowledgeRetriever
from src.models.user import User
from backend.dependencies import get_retriever, get_current_user, require_admin
from backend.schemas.knowledge import (
    DocumentItem,
    SearchResultChunk,
    KnowledgeSearchRequest,
    ReindexResponse,
)

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Base & RAG Index"])


@router.get("/documents", response_model=List[DocumentItem])
async def list_documents(
    current_user: User = Depends(get_current_user),
):
    """List all standard operating procedures and runbooks in the knowledge base."""
    docs: List[DocumentItem] = []
    if settings.KNOWLEDGE_BASE_DIR.exists():
        for f in settings.KNOWLEDGE_BASE_DIR.iterdir():
            if f.is_file() and not f.name.startswith("."):
                stat = f.stat()
                mod_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
                docs.append(
                    DocumentItem(
                        filename=f.name,
                        size_bytes=stat.st_size,
                        modified_at=mod_time,
                        extension=f.suffix.lower(),
                    )
                )
    return docs


@router.get("/documents/{filename}/content")
async def get_document_content(
    filename: str,
    current_user: User = Depends(get_current_user),
):
    """Read the content of a runbook file."""
    file_path = settings.KNOWLEDGE_BASE_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {"filename": filename, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_admin: User = Depends(require_admin),
):
    """Upload a new runbook (.md, .txt, .pdf, .docx) to the knowledge base (Admin only)."""
    allowed_exts = {".md", ".txt", ".pdf", ".docx"}
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(allowed_exts)}",
        )

    safe_filename = Path(file.filename).name
    save_path = settings.KNOWLEDGE_BASE_DIR / safe_filename

    try:
        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)
        return {
            "message": f"Runbook '{safe_filename}' uploaded successfully.",
            "filename": safe_filename,
            "size_bytes": len(content),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


@router.delete("/documents/{filename}")
async def delete_document(
    filename: str,
    current_admin: User = Depends(require_admin),
):
    """Remove a runbook document from the knowledge base directory (Admin only)."""
    file_path = settings.KNOWLEDGE_BASE_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    try:
        file_path.unlink()
        return {"message": f"Document '{filename}' deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.post("/reindex", response_model=ReindexResponse)
async def reindex_knowledge_base(
    current_admin: User = Depends(require_admin),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Trigger full document parsing, text chunking, and FAISS vector index rebuild."""
    try:
        chunk_count = retriever.reindex_all()
        kb_files = [f for f in settings.KNOWLEDGE_BASE_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]
        return ReindexResponse(
            success=True,
            chunks_indexed=chunk_count,
            total_files=len(kb_files),
            message=f"Reindexed {chunk_count} chunks across {len(kb_files)} runbooks into FAISS index.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reindexing failed: {str(e)}")


@router.post("/search", response_model=List[SearchResultChunk])
async def search_knowledge_base(
    req: KnowledgeSearchRequest,
    current_user: User = Depends(get_current_user),
    retriever: KnowledgeRetriever = Depends(get_retriever),
):
    """Semantic vector search testing playground."""
    results = retriever.retrieve(req.query, top_k=req.top_k)
    chunks: List[SearchResultChunk] = []
    for chunk, score in results:
        chunks.append(
            SearchResultChunk(
                chunk_id=chunk.doc_id,
                source=chunk.source,
                title=chunk.title,
                score=round(float(score), 4),
                snippet=chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                text=chunk.text,
            )
        )
    return chunks

