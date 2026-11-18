"""LangChain-compatible Document Loader for IT Knowledge Base.

Loads PDF, DOCX, TXT, and Markdown files into standard LangChain Document objects
with rich metadata tracking.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from config.settings import settings
from src.rag.text_splitter import ApexTextSplitter


def infer_metadata_from_source(source: str) -> Dict[str, str]:
    """Derive IT domain category and subcategory from runbook filename and title."""
    s = str(source).lower()
    if "vpn" in s:
        return {"category": "VPN", "subcategory": "VPN_CONNECTIVITY", "document_type": "troubleshooting_guide"}
    elif any(k in s for k in ["pass", "mfa", "auth", "login", "sso", "entra"]):
        return {"category": "ACCOUNT_AUTHENTICATION", "subcategory": "MFA_AND_PASSWORD", "document_type": "troubleshooting_guide"}
    elif any(k in s for k in ["wifi", "network", "ethernet", "dns", "dhcp"]):
        return {"category": "NETWORK_CONNECTIVITY", "subcategory": "WIFI_AND_NETWORK", "document_type": "troubleshooting_guide"}
    elif any(k in s for k in ["outlook", "email", "teams", "exchange", "calendar"]):
        return {"category": "EMAIL_COLLABORATION", "subcategory": "EMAIL_AND_TEAMS", "document_type": "troubleshooting_guide"}
    elif any(k in s for k in ["printer", "hardware", "dock", "monitor"]):
        return {"category": "HARDWARE", "subcategory": "PRINTER_AND_DOCKS", "document_type": "troubleshooting_guide"}
    elif any(k in s for k in ["crash", "bsod", "blue_screen", "shutdown", "dump"]):
        return {"category": "OPERATING_SYSTEM", "subcategory": "UNEXPECTED_SHUTDOWN", "document_type": "troubleshooting_guide"}
    elif any(k in s for k in ["permission", "access", "shared_drive", "folder", "sharepoint"]):
        return {"category": "ACCESS_PERMISSIONS", "subcategory": "SHARED_FOLDER_PERMISSIONS", "document_type": "troubleshooting_guide"}
    elif any(k in s for k in ["cyber", "security", "phish", "malware", "threat"]):
        return {"category": "CYBERSECURITY", "subcategory": "PHISHING_AND_THREATS", "document_type": "troubleshooting_guide"}
    elif any(k in s for k in ["cloud", "database", "sql"]):
        return {"category": "CLOUD_SERVICES", "subcategory": "DATABASE_AND_CLOUD", "document_type": "troubleshooting_guide"}
    elif "software" in s:
        return {"category": "SOFTWARE_APPLICATION", "subcategory": "SOFTWARE_DEPLOYMENT", "document_type": "troubleshooting_guide"}
    return {"category": "OTHER_IT_SUPPORT", "subcategory": "GENERAL_IT", "document_type": "troubleshooting_guide"}


class DocumentChunk:
    """Backward-compatible adapter representing a chunk of text with rich metadata."""

    def __init__(
        self,
        doc_id: str,
        source: str,
        title: str,
        text: str,
        chunk_index: int,
        category: str = "OTHER_IT_SUPPORT",
        subcategory: str = "GENERAL_IT",
        document_type: str = "troubleshooting_guide",
    ):
        self.doc_id = doc_id
        self.source = source
        self.title = title
        self.text = text
        self.chunk_index = chunk_index
        self.category = category
        self.subcategory = subcategory
        self.document_type = document_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "source": self.source,
            "title": self.title,
            "text": self.text,
            "chunk_index": self.chunk_index,
            "category": self.category,
            "subcategory": self.subcategory,
            "document_type": self.document_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DocumentChunk:
        return cls(
            doc_id=data.get("doc_id", ""),
            source=data.get("source", ""),
            title=data.get("title", ""),
            text=data.get("text", ""),
            chunk_index=data.get("chunk_index", 0),
            category=data.get("category", "OTHER_IT_SUPPORT"),
            subcategory=data.get("subcategory", "GENERAL_IT"),
            document_type=data.get("document_type", "troubleshooting_guide"),
        )

    @classmethod
    def from_lc_document(cls, doc: Document, index: int = 0) -> DocumentChunk:
        source = doc.metadata.get("source", "unknown")
        title = doc.metadata.get("title", Path(source).stem.replace("_", " ").title())
        inferred = infer_metadata_from_source(source)
        category = doc.metadata.get("category") or inferred["category"]
        subcategory = doc.metadata.get("subcategory") or inferred["subcategory"]
        document_type = doc.metadata.get("document_type") or inferred["document_type"]
        return cls(
            doc_id=f"{Path(source).name}_chunk_{index}",
            source=Path(source).name,
            title=title,
            text=doc.page_content,
            chunk_index=doc.metadata.get("chunk_index", index),
            category=category,
            subcategory=subcategory,
            document_type=document_type,
        )


class DocumentLoader:
    """Loads and chunks IT documents into LangChain Document objects."""

    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.splitter = ApexTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)

    def load_single_file(self, file_path: Path) -> List[Document]:
        """Load a file into LangChain Document objects based on extension."""
        ext = file_path.suffix.lower()
        title = file_path.stem.replace("_", " ").title()
        docs: List[Document] = []

        if ext == ".pdf":
            try:
                from langchain_community.document_loaders import PyPDFLoader
                loader = PyPDFLoader(str(file_path))
                raw_docs = loader.load()
                for d in raw_docs:
                    d.metadata["title"] = title
                    d.metadata["source"] = file_path.name
                docs = raw_docs
            except Exception:
                try:
                    import pypdf
                    reader = pypdf.PdfReader(str(file_path))
                    for idx, page in enumerate(reader.pages):
                        text = page.extract_text() or ""
                        if text.strip():
                            docs.append(Document(
                                page_content=text,
                                metadata={"source": file_path.name, "title": title, "page": idx + 1}
                            ))
                except Exception:
                    pass

        elif ext == ".docx":
            try:
                from langchain_community.document_loaders import Docx2txtLoader
                loader = Docx2txtLoader(str(file_path))
                raw_docs = loader.load()
                for d in raw_docs:
                    d.metadata["title"] = title
                    d.metadata["source"] = file_path.name
                docs = raw_docs
            except Exception:
                try:
                    import docx2txt
                    text = docx2txt.process(str(file_path))
                    if text.strip():
                        docs.append(Document(
                            page_content=text,
                            metadata={"source": file_path.name, "title": title}
                        ))
                except Exception:
                    pass

        elif ext in (".md", ".txt", ".markdown", ".rst"):
            try:
                from langchain_community.document_loaders import TextLoader
                loader = TextLoader(str(file_path), encoding="utf-8")
                raw_docs = loader.load()
                for d in raw_docs:
                    d.metadata["title"] = title
                    d.metadata["source"] = file_path.name
                docs = raw_docs
            except Exception:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        text = f.read()
                    if text.strip():
                        docs.append(Document(
                            page_content=text,
                            metadata={"source": file_path.name, "title": title}
                        ))
                except Exception:
                    pass

        inferred = infer_metadata_from_source(file_path.name)
        for d in docs:
            d.metadata.setdefault("category", inferred["category"])
            d.metadata.setdefault("subcategory", inferred["subcategory"])
            d.metadata.setdefault("document_type", inferred["document_type"])

        return self.splitter.split_documents(docs)

    def load_file(self, file_path: Path) -> str:
        """Legacy helper returning full raw text of a file."""
        ext = file_path.suffix.lower()
        if ext in (".md", ".txt", ".markdown"):
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        docs = self.load_single_file(file_path)
        return "\n\n".join([d.page_content for d in docs])

    def chunk_text(self, text: str, source_name: str, title: str) -> List[DocumentChunk]:
        """Legacy helper chunking raw string into DocumentChunk objects."""
        doc = Document(page_content=text, metadata={"source": source_name, "title": title})
        chunks = self.splitter.split_documents([doc])
        return [DocumentChunk.from_lc_document(c, idx) for idx, c in enumerate(chunks)]

    def load_directory(self, dir_path: Optional[Path] = None) -> List[DocumentChunk]:
        """Scan knowledge base directory and return chunks."""
        target_dir = dir_path or settings.KNOWLEDGE_BASE_DIR
        target_dir.mkdir(parents=True, exist_ok=True)

        all_chunks: List[DocumentChunk] = []
        for root, _, files in os.walk(target_dir):
            for file in files:
                file_path = Path(root) / file
                if file.startswith(".") or file_path.suffix.lower() not in (
                    ".md", ".txt", ".pdf", ".docx", ".markdown"
                ):
                    continue
                docs = self.load_single_file(file_path)
                chunks = [DocumentChunk.from_lc_document(d, idx) for idx, d in enumerate(docs)]
                all_chunks.extend(chunks)

        return all_chunks

    def load_documents_directory(self, dir_path: Optional[Path] = None) -> List[Document]:
        """Scan directory and return LangChain Document objects."""
        target_dir = dir_path or settings.KNOWLEDGE_BASE_DIR
        target_dir.mkdir(parents=True, exist_ok=True)

        all_docs: List[Document] = []
        for root, _, files in os.walk(target_dir):
            for file in files:
                file_path = Path(root) / file
                if file.startswith(".") or file_path.suffix.lower() not in (
                    ".md", ".txt", ".pdf", ".docx", ".markdown"
                ):
                    continue
                docs = self.load_single_file(file_path)
                all_docs.extend(docs)

        return all_docs
