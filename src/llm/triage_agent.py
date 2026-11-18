"""Unified IT Support and Triage Agent coordinating LangGraph, RAG, Gemini LLM, and offline fallbacks."""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from config import settings
from src.models.ticket import Ticket, TicketMessage, TriageResult, TicketCategory, TicketPriority
from src.rag.retriever import KnowledgeRetriever
from src.llm.gemini_client import GeminiClient
from src.llm.offline_engine import OfflineDiagnosticEngine
from src.llm.prompts import RESOLUTION_SUMMARY_PROMPT


class SupportTriageAgent:
    """End-to-end agent for IT chat troubleshooting, automated ticket triage,
    LangGraph agentic execution, and technician resolution note drafting.
    """

    def __init__(
        self,
        retriever: Optional[KnowledgeRetriever] = None,
        gemini_client: Optional[GeminiClient] = None,
        offline_engine: Optional[OfflineDiagnosticEngine] = None,
    ):
        self.retriever = retriever or KnowledgeRetriever()
        self.gemini_client = gemini_client or GeminiClient()
        self.offline_engine = offline_engine or OfflineDiagnosticEngine()

    def run_agent(
        self,
        user_message: str,
        session_id: str = "default_session",
        thread_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        approval_status: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute stateful LangGraph agentic workflow with SQLite checkpointing."""
        from src.agents.graph import run_support_agent

        return run_support_agent(
            message=user_message,
            session_id=session_id,
            thread_id=thread_id,
            conversation_history=conversation_history,
            approval_status=approval_status,
            **kwargs,
        )

    def answer_query(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        session_id: str = "default_session",
    ) -> Dict[str, Any]:
        """Execute query answering via LangGraph agentic pipeline."""
        try:
            from src.agents.graph import run_support_agent

            state = run_support_agent(
                message=user_message,
                session_id=session_id,
                conversation_history=conversation_history,
            )
            raw_docs = state.get("retrieved_documents", [])
            sources = [
                {
                    "source": d.get("source", "knowledge_base"),
                    "title": d.get("title", "Runbook Article"),
                    "score": round(float(d.get("score", 0.0)), 2),
                    "snippet": (
                        d.get("text", "")[:180] + "..."
                        if len(d.get("text", "")) > 180
                        else d.get("text", "")
                    ),
                }
                for d in raw_docs
            ]
            return {
                "answer": state.get("generated_answer") or "No response generated.",
                "sources": sources,
                "used_gemini": state.get("execution_mode") == "gemini",
                "query_type": state.get("query_type", "troubleshooting"),
                "approval_status": state.get("approval_status"),
                "ticket_id": state.get("ticket_id"),
                "assigned_team": state.get("assigned_team"),
                "state": state,
            }
        except Exception:
            # Fallback directly to domain classifier + retriever + offline engine
            from src.llm.domain_classifier import DomainClassifier, OUT_OF_SCOPE_MESSAGE
            classifier = DomainClassifier(gemini_client=self.gemini_client)
            classification = classifier.classify(user_message)

            if not classification.is_it_related or classification.category == "OUT_OF_SCOPE":
                return {
                    "answer": OUT_OF_SCOPE_MESSAGE,
                    "sources": [],
                    "used_gemini": False,
                    "query_type": "out_of_scope",
                    "approval_status": None,
                    "ticket_id": None,
                    "assigned_team": None,
                    "state": {"is_out_of_scope": True},
                }

            retrieved_chunks = self.retriever.retrieve(
                user_message,
                top_k=settings.TOP_K_RETRIEVAL,
                category=classification.category,
            )
            rag_context = self.retriever.format_context(retrieved_chunks)

            answer = None
            used_gemini = False
            if self.gemini_client.is_configured():
                answer = self.gemini_client.generate_response(
                    user_message=user_message,
                    conversation_history=conversation_history,
                    rag_context=rag_context,
                )
                if answer:
                    used_gemini = True

            if not answer:
                answer = self.offline_engine.synthesize_response(
                    user_query=user_message,
                    retrieved_chunks=retrieved_chunks,
                    category=classification.category,
                )

            return {
                "answer": answer,
                "sources": [
                    {
                        "source": chunk.source,
                        "title": chunk.title,
                        "score": round(score, 2),
                        "snippet": chunk.text[:180] + "..." if len(chunk.text) > 180 else chunk.text,
                    }
                    for chunk, score in retrieved_chunks
                ],
                "used_gemini": used_gemini,
                "query_type": "troubleshooting",
                "approval_status": None,
                "ticket_id": None,
                "assigned_team": None,
                "state": {},
            }

    def triage_ticket(self, description: str) -> TriageResult:
        """Classify category, priority, and immediate steps for ticket creation."""
        # Try Gemini LLM first
        if self.gemini_client.is_configured():
            triage_data = self.gemini_client.triage_ticket(description)
            if triage_data and isinstance(triage_data, dict):
                try:
                    category_str = triage_data.get("category", "")
                    category = next(
                        (c for c in TicketCategory if c.value.lower() == category_str.lower()),
                        TicketCategory.OTHER,
                    )
                    priority_str = triage_data.get("priority", "")
                    priority = next(
                        (p for p in TicketPriority if p.value.lower() == priority_str.lower()),
                        TicketPriority.MEDIUM,
                    )
                    return TriageResult(
                        category=category,
                        priority=priority,
                        summary=triage_data.get("summary", description[:60]),
                        confidence=float(triage_data.get("confidence", 0.95)),
                        key_entities=triage_data.get("key_entities", []),
                        immediate_actions=triage_data.get("immediate_actions", []),
                        recommended_team=triage_data.get("recommended_team", "Tier 1 Service Desk"),
                    )
                except Exception:
                    pass

        # Offline fallback triage
        return self.offline_engine.triage_description(description)

    def generate_resolution_summary(
        self, ticket: Ticket, messages: List[TicketMessage]
    ) -> str:
        """Draft a formal resolution note for technician closing the ticket."""
        formatted_conv = "\n".join(
            [f"[{m.sender.upper()}] ({m.timestamp[:16]}): {m.message}" for m in messages]
        )
        prompt = RESOLUTION_SUMMARY_PROMPT.format(
            title=ticket.title,
            description=ticket.description,
            category=ticket.category.value,
            technician=ticket.assigned_to or "Technician",
            conversation=formatted_conv,
        )

        if self.gemini_client.is_configured():
            summary = self.gemini_client.summarize_resolution(prompt)
            if summary:
                return summary

        # Offline heuristic summary
        return (
            f"Verified issue regarding '{ticket.title}'. Root cause identified as configuration or transient error. "
            f"Remediation procedures from '{ticket.category.value}' runbook executed successfully. "
            f"User confirmed system restored to normal operational parameters."
        )
