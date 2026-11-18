"""The 12 LangGraph Agentic Workflow Nodes for QuickFixer."""

from __future__ import annotations

import re
from typing import Dict, Any, List
from src.agents.state import SupportState
from src.agents.tools import (
    get_tool_db,
    get_tool_retriever,
    get_ticket_status,
    create_it_ticket,
    generate_resolution_note,
)
from src.llm.gemini_client import GeminiClient
from src.llm.offline_engine import OfflineDiagnosticEngine
from src.llm.domain_classifier import (
    DomainClassifier,
    DomainClassification,
    ITDomainCategory,
    OUT_OF_SCOPE_MESSAGE,
)
from src.llm.query_rewriter import QueryRewriter
from src.models.ticket import (
    Ticket,
    TicketCategory,
    TicketPriority,
    TicketStatus,
    TicketMessage,
)

# Global service singletons for nodes
_gemini: GeminiClient | None = None
_offline: OfflineDiagnosticEngine | None = None
_classifier: DomainClassifier | None = None
_rewriter: QueryRewriter | None = None


def get_node_gemini() -> GeminiClient:
    global _gemini
    if _gemini is None:
        _gemini = GeminiClient()
    return _gemini


def get_node_offline() -> OfflineDiagnosticEngine:
    global _offline
    if _offline is None:
        _offline = OfflineDiagnosticEngine()
    return _offline


def get_node_classifier() -> DomainClassifier:
    global _classifier
    if _classifier is None:
        _classifier = DomainClassifier(gemini_client=get_node_gemini())
    return _classifier


def get_node_rewriter() -> QueryRewriter:
    global _rewriter
    if _rewriter is None:
        _rewriter = QueryRewriter(gemini_client=get_node_gemini())
    return _rewriter


# -------------------------------------------------------------------------
# NODE 1: RECEIVE QUERY
# -------------------------------------------------------------------------
def receive_query_node(state: SupportState) -> Dict[str, Any]:
    """Ingest employee input and initialize workflow state context."""
    user_id = state.get("user_id") or "emp_default"
    session_id = state.get("session_id") or "sess_default"
    user_name = state.get("user_name") or "Employee"
    user_email = state.get("user_email") or "employee@company.com"
    device_info = state.get("device_info") or "Enterprise Workstation"
    question = (state.get("question") or "").strip()

    history = state.get("conversation_history", [])
    if question and not any(h.get("content") == question and h.get("role") == "user" for h in history[-2:]):
        history = list(history) + [{"role": "user", "content": question}]

    return {
        "user_id": user_id,
        "session_id": session_id,
        "user_name": user_name,
        "user_email": user_email,
        "device_info": device_info,
        "question": question,
        "conversation_history": history,
        "error_message": None,
    }


# -------------------------------------------------------------------------
# NODE 2: CLASSIFY QUERY & OUT-OF-SCOPE DETECTION
# -------------------------------------------------------------------------
def classify_query_node(state: SupportState) -> Dict[str, Any]:
    """Identify query domain, detect out-of-scope queries, and rewrite informal issues."""
    question = state.get("question", "")

    # Check if confirming or declining a pending approval
    if state.get("approval_status") == "pending":
        q_clean = question.strip().lower()
        if any(w in q_clean for w in ["yes", "approve", "approved", "confirm", "proceed", "go ahead", "create", "submit"]):
            return {"query_type": "ticket_creation", "approval_status": "approved"}
        elif any(w in q_clean for w in ["no", "cancel", "stop", "abort", "reject"]):
            return {
                "query_type": "troubleshooting",
                "approval_status": "rejected",
                "generated_answer": "Ticket creation cancelled. How else can I assist you?",
            }

    classifier = get_node_classifier()
    rewriter = get_node_rewriter()

    # Domain classification
    classification = classifier.classify(question)

    # 1. OUT OF SCOPE DETECTION
    if not classification.is_it_related or classification.category == ITDomainCategory.OUT_OF_SCOPE.value:
        return {
            "query_type": "out_of_scope",
            "is_out_of_scope": True,
            "domain_classification": classification.model_dump(),
            "generated_answer": OUT_OF_SCOPE_MESSAGE,
        }

    # 1B. NEEDS CLARIFICATION FOR VAGUE / AMBIGUOUS QUERIES
    if classification.category == ITDomainCategory.NEEDS_CLARIFICATION.value or classification.intent == "NEEDS_CLARIFICATION":
        clarification_msg = (
            "I would be glad to help you resolve your technical issue! "
            "Could you please specify which type of IT problem you are experiencing?\n\n"
            "**Common Problem Categories:**\n"
            "- 🔑 **Account & Authentication:** Windows login, password reset, MFA / Microsoft Authenticator OTP\n"
            "- 🌐 **Network & Connectivity:** Wi-Fi dropping, no internet, Ethernet connection error\n"
            "- 🔒 **VPN Connection:** Cisco AnyConnect or GlobalProtect timed out / connection failure\n"
            "- ✉️ **Email & Teams:** Outlook crashes, emails not sending/receiving, Teams audio/mic issues\n"
            "- 💻 **Operating System & Crashes:** Computer freezes, blue screen (BSOD), unexpected computer shutdown\n"
            "- 🖨️ **Hardware & Peripherals:** Printer offline, paper jam, docking station, external monitor\n"
            "- 📦 **Software & Applications:** Application crashes, software install error, admin rights (EPM)\n"
            "- 📁 **Access & Permissions:** Shared network folder 'Access Denied', SharePoint permission request\n\n"
            "Please describe the specific symptoms, application, or error message you're seeing!"
        )
        return {
            "query_type": "clarification_needed",
            "is_out_of_scope": False,
            "domain_classification": classification.model_dump(),
            "generated_answer": clarification_msg,
            "issue_category": "NEEDS_CLARIFICATION",
            "retrieved_documents": [],
            "retrieval_scores": [],
        }

    # 2. INTELLIGENT QUERY REWRITING
    rewritten_query = rewriter.rewrite(question, classification)

    # 3. INTENT DETERMINATION
    q_lower = question.lower()
    if re.search(r"\btick-\d+\b", q_lower) or any(w in q_lower for w in ["status of", "check ticket"]):
        query_type = "ticket_status"
    elif any(w in q_lower for w in ["phishing", "ransomware", "malware", "virus", "security alert"]):
        query_type = "security_incident"
    elif re.search(r"\b(create|open|raise|submit|escalate|log)\b.*\b(ticket|incident|case)\b", q_lower):
        query_type = "ticket_creation"
    elif any(w in q_lower for w in ["what is the policy", "office hours", "how do i request", "guideline"]):
        query_type = "general_inquiry"
    else:
        intent_map = {
            "TICKET_STATUS": "ticket_status",
            "SECURITY_INCIDENT": "security_incident",
            "TICKET_CREATION": "ticket_creation",
            "GENERAL_INQUIRY": "general_inquiry",
            "TROUBLESHOOTING": "troubleshooting",
        }
        query_type = intent_map.get(classification.intent, "troubleshooting")

    return {
        "query_type": query_type,
        "is_out_of_scope": False,
        "rewritten_query": rewritten_query,
        "domain_classification": classification.model_dump(),
        "issue_category": classification.category,
    }


# -------------------------------------------------------------------------
# NODE 2B: OUT OF SCOPE GUARDRAIL
# -------------------------------------------------------------------------
def out_of_scope_node(state: SupportState) -> Dict[str, Any]:
    """Handle non-IT questions or vague clarification requests with polite guardrail message and terminate workflow."""
    return {
        "generated_answer": state.get("generated_answer") or OUT_OF_SCOPE_MESSAGE,
        "execution_mode": "guardrail",
        "retrieved_documents": [],
        "retrieval_scores": [],
        "ticket_required": False,
    }


# -------------------------------------------------------------------------
# NODE 3: RETRIEVE KNOWLEDGE
# -------------------------------------------------------------------------
def retrieve_knowledge_node(state: SupportState) -> Dict[str, Any]:
    """Retrieve relevant IT runbooks and troubleshooting guides using LangChain FAISS."""
    search_query = state.get("rewritten_query") or state.get("question", "")
    category = state.get("domain_classification", {}).get("category")
    retriever = get_tool_retriever()

    results = retriever.retrieve(search_query, top_k=3, category=category)
    doc_dicts = [
        {
            "doc_id": c.doc_id,
            "source": c.source,
            "title": c.title,
            "text": c.text,
            "score": round(score, 3),
            "category": getattr(c, "category", ""),
            "subcategory": getattr(c, "subcategory", ""),
        }
        for c, score in results
    ]
    scores = [round(score, 3) for _, score in results]

    return {
        "retrieved_documents": doc_dicts,
        "retrieval_scores": scores,
    }


# -------------------------------------------------------------------------
# NODE 4: GENERATE RESPONSE
# -------------------------------------------------------------------------
def generate_response_node(state: SupportState) -> Dict[str, Any]:
    """Generate grounded step-by-step troubleshooting response with source citations."""
    if state.get("is_out_of_scope"):
        return {
            "generated_answer": OUT_OF_SCOPE_MESSAGE,
            "execution_mode": "guardrail",
            "ticket_required": False,
        }

    question = state.get("question", "")
    rewritten_query = state.get("rewritten_query", question)
    category = state.get("domain_classification", {}).get("category")
    history = state.get("conversation_history", [])
    doc_dicts = state.get("retrieved_documents", [])
    gemini = get_node_gemini()
    offline = get_node_offline()

    # Format context string
    retriever = get_tool_retriever()
    context_text = retriever.format_context(
        [(type("C", (), {"source": d["source"], "title": d["title"], "text": d["text"]})(), d["score"]) for d in doc_dicts]
    )

    answer = None
    mode = "offline"

    if gemini.is_configured():
        enhanced_context = f"Domain Category: {category or 'General IT'}\nTechnical Diagnosis Target: {rewritten_query}\n\n{context_text}"
        answer = gemini.generate_response(
            user_message=question,
            conversation_history=history[:-1] if len(history) > 1 else [],
            rag_context=enhanced_context,
        )
        if answer:
            mode = "gemini"

    if not answer:
        # Reconstruct chunks for offline synthesizer
        loader_chunks = [
            type("Chunk", (), {"title": d["title"], "source": d["source"], "text": d["text"]})()
            for d in doc_dicts
        ]
        chunk_tuples = [(c, d["score"]) for c, d in zip(loader_chunks, doc_dicts)]
        answer = offline.synthesize_response(
            user_query=question,
            retrieved_chunks=chunk_tuples,
            category=category,
        )
        mode = "offline"

    # Final Answer Relevance Validation (Section 9)
    from src.llm.response_validator import ResponseValidator
    classification_dict = state.get("domain_classification")
    classification_obj = DomainClassification(**classification_dict) if classification_dict else None
    validation = ResponseValidator.validate_and_sanitize(
        answer=answer,
        query=question,
        classification=classification_obj,
        retrieved_docs=doc_dicts,
        retrieval_scores=state.get("retrieval_scores", []),
    )
    validated_answer = validation["sanitized_answer"]

    # Append prompt asking if issue was resolved
    follow_up = (
        "\n\n---\n"
        "**Did this resolve your issue?**\n"
        "- Reply **'Yes'** if your issue is resolved.\n"
        "- Reply **'No'** or **'Escalate'** to automatically create an IT Support Ticket."
    )
    full_answer = validated_answer + follow_up

    return {
        "generated_answer": full_answer,
        "execution_mode": mode,
        "ticket_required": False,
    }


# -------------------------------------------------------------------------
# NODE 5: CHECK RESOLUTION
# -------------------------------------------------------------------------
def check_resolution_node(state: SupportState) -> Dict[str, Any]:
    """Check user confirmation: if resolved end session; if unresolved initiate ticket triage."""
    question = state.get("question", "").strip().lower()

    resolved_keywords = ["yes", "resolved", "fixed", "works now", "working now", "solved", "all good", "thank you"]
    unresolved_keywords = ["no", "not working", "still broken", "escalate", "create ticket", "open ticket", "didn't work", "fail"]

    if any(k in question for k in resolved_keywords):
        return {
            "resolution_confirmed": True,
            "ticket_required": False,
            "generated_answer": "🎉 Wonderful! I'm glad we could resolve your technical issue. Have a great and productive day!",
        }
    elif any(k in question for k in unresolved_keywords):
        return {
            "resolution_confirmed": False,
            "ticket_required": True,
        }
    else:
        # Ambiguous input, default to offering ticket escalation
        return {
            "resolution_confirmed": False,
            "ticket_required": True,
        }


# -------------------------------------------------------------------------
# NODE 6: TICKET TRIAGE
# -------------------------------------------------------------------------
def ticket_triage_node(state: SupportState) -> Dict[str, Any]:
    """Analyze incident and determine Category, Priority, Entities, Urgency, and Team."""
    question = state.get("question", "")
    history = state.get("conversation_history", [])

    # Combine description from history
    user_messages = [m.get("content", "") for m in history if m.get("role") == "user"]
    full_desc = "\n".join(user_messages) if user_messages else question

    gemini = get_node_gemini()
    offline = get_node_offline()

    triage_dict = None
    if gemini.is_configured():
        triage_dict = gemini.triage_ticket(full_desc)

    if not triage_dict:
        triage_obj = offline.triage_description(full_desc)
        triage_dict = triage_obj.model_dump()

    category = triage_dict.get("category", "General IT Inquiry")
    priority = triage_dict.get("priority", "Medium")
    if hasattr(category, "value"):
        category = category.value
    if hasattr(priority, "value"):
        priority = priority.value
    category = str(category)
    priority = str(priority)
    summary = triage_dict.get("summary", question[:60])
    entities = triage_dict.get("key_entities", [])
    immediate_actions = triage_dict.get("immediate_actions", [])
    recommended_team = triage_dict.get("recommended_team", "Tier 1 Service Desk")

    # Deterministic safety rule: Never downgrade clear critical outages
    desc_lower = full_desc.lower()
    if any(k in desc_lower for k in ["entire team", "company wide", "production down", "ransomware", "breach"]):
        priority = "Critical"
    elif any(k in desc_lower for k in ["cannot work", "blocked", "urgent", "bsod", "blue screen"]):
        if priority == "Low":
            priority = "High"

    return {
        "issue_category": category,
        "priority": priority,
        "triage_summary": summary,
        "key_entities": entities,
        "immediate_actions": immediate_actions,
        "assigned_team": recommended_team,
        "approval_status": "pending",
    }


# -------------------------------------------------------------------------
# NODE 7: HUMAN APPROVAL
# -------------------------------------------------------------------------
def human_approval_node(state: SupportState) -> Dict[str, Any]:
    """Present triage details to employee and seek confirmation before ticket insertion."""
    summary = state.get("triage_summary", "Technical Incident")
    category = state.get("issue_category", "General IT Inquiry")
    priority = state.get("priority", "Medium")
    team = state.get("assigned_team", "Tier 1 Service Desk")
    status = state.get("approval_status", "pending")

    if status == "approved":
        return {"approval_status": "approved", "interrupted_for_approval": False}

    approval_msg = (
        f"### 📋 Support Ticket Approval Request\n\n"
        f"Before submitting your ticket, please review the AI Triage details:\n"
        f"- **Issue Title:** `{summary}`\n"
        f"- **Predicted Category:** `{category}`\n"
        f"- **Assigned Priority:** `{priority}`\n"
        f"- **Routing Queue:** `{team}`\n\n"
        f"> Please confirm whether you would like to proceed with creating this ticket."
    )

    return {
        "generated_answer": approval_msg,
        "approval_status": "pending",
        "interrupted_for_approval": True,
    }


# -------------------------------------------------------------------------
# NODE 8: CREATE TICKET
# -------------------------------------------------------------------------
def create_ticket_node(state: SupportState) -> Dict[str, Any]:
    """Insert ticket into SQLite database idempotently, preventing duplicates."""
    # Prevent duplicate ticket creation if already created in this thread
    if state.get("ticket_id"):
        return {"ticket_id": state["ticket_id"]}

    db = get_tool_db()
    summary = state.get("triage_summary") or state.get("question", "IT Support Ticket")[:60]
    history = state.get("conversation_history", [])
    user_msgs = [m.get("content", "") for m in history if m.get("role") == "user"]
    desc = "\n\n".join(user_msgs) if user_msgs else state.get("question", "")

    cat_str = state.get("issue_category", "General IT Inquiry")
    prio_str = state.get("priority", "Medium")
    team_str = state.get("assigned_team", "Tier 1 Service Desk")

    matched_cat = next((c for c in TicketCategory if c.value.lower() == cat_str.lower()), TicketCategory.OTHER)
    matched_prio = next((p for p in TicketPriority if p.value.lower() == prio_str.lower()), TicketPriority.MEDIUM)

    ticket = Ticket(
        id="",
        title=f"Incident: {summary}",
        description=desc,
        category=matched_cat,
        priority=matched_prio,
        status=TicketStatus.OPEN,
        user_name=state.get("user_name", "Employee"),
        user_email=state.get("user_email", "employee@company.com"),
        device_info=state.get("device_info", "Enterprise Workstation"),
        assigned_to=team_str,
        ai_diagnosis=f"Triage Team: {team_str} | Priority: {matched_prio.value}",
        suggested_steps="\n".join([f"- {a}" for a in state.get("immediate_actions", [])]),
    )

    created = db.create_ticket(ticket)
    confirmation = (
        f"✅ **Support Ticket Created Successfully!**\n\n"
        f"- **Ticket ID:** `{created.id}`\n"
        f"- **Title:** {created.title}\n"
        f"- **Priority:** `{created.priority.value}`\n"
        f"- **Assigned Queue:** `{team_str}`\n"
        f"- **Status:** `{created.status.value}`\n\n"
        f"You can check the status of your ticket at any time by asking: *\"What is the status of {created.id}?\"*"
    )

    return {
        "ticket_id": created.id,
        "generated_answer": confirmation,
        "approval_status": "approved",
        "interrupted_for_approval": False,
    }


# -------------------------------------------------------------------------
# NODE 9: ROUTE TICKET
# -------------------------------------------------------------------------
def route_ticket_node(state: SupportState) -> Dict[str, Any]:
    """Map issue category to designated engineering team."""
    category = state.get("issue_category", "")

    team_routing_map = {
        TicketCategory.NETWORK.value: "NetOps Infrastructure",
        TicketCategory.ACCOUNT.value: "Identity & Access Management (IAM)",
        TicketCategory.SECURITY.value: "Security Operations Center (SOC)",
        TicketCategory.HARDWARE.value: "Deskside & Hardware Support",
        TicketCategory.SOFTWARE.value: "Endpoint Management",
        TicketCategory.EMAIL.value: "Messaging & Collaboration",
        TicketCategory.OTHER.value: "Tier 1 Service Desk",
    }
    assigned = team_routing_map.get(category, "Tier 1 Service Desk")
    return {"assigned_team": assigned}


# -------------------------------------------------------------------------
# NODE 10: TICKET STATUS LOOKUP
# -------------------------------------------------------------------------
def ticket_status_lookup_node(state: SupportState) -> Dict[str, Any]:
    """Extract Ticket ID from query and fetch live status."""
    question = state.get("question", "")
    match = re.search(r"\bTICK-\d+\b", question, re.IGNORECASE)
    if match:
        ticket_id = match.group(0).upper()
        status_info = get_ticket_status.invoke({"ticket_id": ticket_id})
        answer = f"### 🎫 Ticket Status Report\n\n```yaml\n{status_info}\n```"
    else:
        answer = "Please provide a valid Ticket ID (e.g., `TICK-1001`) to look up its status."

    return {
        "generated_answer": answer,
        "ticket_required": False,
    }


# -------------------------------------------------------------------------
# NODE 11: RESOLUTION SUMMARY
# -------------------------------------------------------------------------
def resolution_summary_node(state: SupportState) -> Dict[str, Any]:
    """Generate formal ITIL resolution note for technician record-keeping."""
    ticket_id = state.get("ticket_id") or ""
    if not ticket_id:
        match = re.search(r"\bTICK-\d+\b", state.get("question", ""), re.IGNORECASE)
        if match:
            ticket_id = match.group(0).upper()

    if ticket_id:
        note = generate_resolution_note.invoke({"ticket_id": ticket_id})
        answer = f"### 📝 Draft ITIL Resolution Note\n\n{note}"
    else:
        answer = "No active ticket ID identified to generate resolution summary."

    return {"generated_answer": answer}


# -------------------------------------------------------------------------
# NODE 12: END
# -------------------------------------------------------------------------
def end_node(state: SupportState) -> Dict[str, Any]:
    """Finalize execution and ensure conversation history is updated with assistant response."""
    history = list(state.get("conversation_history", []))
    answer = state.get("generated_answer", "")
    if answer and not any(h.get("content") == answer and h.get("role") == "assistant" for h in history[-2:]):
        history.append({"role": "assistant", "content": answer})

    return {
        "conversation_history": history,
    }
