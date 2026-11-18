"""LangChain Google Gemini LLM Client for QuickFixer.

Uses ChatGoogleGenerativeAI with structured output, retries,
and safe offline fallback handling.
"""

from __future__ import annotations

import json
import re
import warnings
from typing import List, Dict, Any, Optional

warnings.filterwarnings("ignore", category=FutureWarning)

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config.settings import settings
from src.llm.prompts import (
    SYSTEM_SUPPORT_PROMPT,
    TRIAGE_SYSTEM_PROMPT,
    QUERY_CLASSIFICATION_PROMPT,
    RESOLUTION_SUMMARY_PROMPT,
)
from src.models.ticket import TriageResult


class GeminiClient:
    """Wrapper around LangChain's ChatGoogleGenerativeAI with resilience and fallback."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self.temperature = temperature if temperature is not None else settings.GEMINI_TEMPERATURE
        self.timeout = timeout or settings.GEMINI_TIMEOUT
        self.max_retries = max_retries or settings.GEMINI_MAX_RETRIES
        self.llm = None
        self._init_model()

    def _init_model(self) -> None:
        """Initialize ChatGoogleGenerativeAI if API key is provided."""
        if not self.api_key:
            self.llm = None
            return

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            self.llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=self.api_key,
                temperature=self.temperature,
                timeout=self.timeout,
                max_retries=self.max_retries,
            )
        except Exception:
            self.llm = None

    def is_configured(self) -> bool:
        """Check if Gemini client is active with a valid configuration."""
        return bool(self.api_key) and self.llm is not None

    def update_key(self, api_key: str) -> bool:
        """Dynamically update API key at runtime."""
        clean_key = api_key.strip() if api_key else ""
        if not clean_key:
            self.api_key = None
            self.llm = None
            return False

        self.api_key = clean_key
        self._init_model()
        return self.is_configured()

    def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        rag_context: str = "",
    ) -> Optional[str]:
        """Generate conversational troubleshooting answer with RAG evidence."""
        if not self.is_configured() or self.llm is None:
            return None

        try:
            system_text = SYSTEM_SUPPORT_PROMPT.format(context=rag_context)
            messages = [SystemMessage(content=system_text)]

            if conversation_history:
                for msg in conversation_history:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        messages.append(HumanMessage(content=content))
                    else:
                        messages.append(AIMessage(content=content))

            messages.append(HumanMessage(content=user_message))
            response = self.llm.invoke(messages)
            return response.content if response and response.content else None

        except Exception:
            return None

    def classify_query_intent(self, query: str) -> Optional[str]:
        """Classify user message intent into one of 5 supported intents."""
        if not self.is_configured() or self.llm is None:
            return None

        try:
            messages = [
                SystemMessage(content=QUERY_CLASSIFICATION_PROMPT),
                HumanMessage(content=f"Classify this query: {query}"),
            ]
            response = self.llm.invoke(messages)
            if response and response.content:
                text = response.content.strip().lower()
                for intent in ("troubleshooting", "ticket_creation", "ticket_status", "security_incident", "general_inquiry"):
                    if intent in text:
                        return intent
            return "troubleshooting"
        except Exception:
            return None

    def triage_ticket(self, description: str) -> Optional[Dict[str, Any]]:
        """Classify issue description into structured ITIL ticket properties."""
        if not self.is_configured() or self.llm is None:
            return None

        # Attempt structured output using Pydantic schema first
        try:
            structured_llm = self.llm.with_structured_output(TriageResult)
            result = structured_llm.invoke([
                SystemMessage(content=TRIAGE_SYSTEM_PROMPT),
                HumanMessage(content=f"Analyze and triage this IT issue:\n\n{description}"),
            ])
            if isinstance(result, TriageResult):
                return result.model_dump()
            elif isinstance(result, dict):
                return result
        except Exception:
            pass

        # Fallback to direct prompt with JSON extraction
        try:
            messages = [
                SystemMessage(content=TRIAGE_SYSTEM_PROMPT + "\nOutput raw JSON only."),
                HumanMessage(content=f"Analyze and triage this issue:\n\n{description}"),
            ]
            response = self.llm.invoke(messages)
            if response and response.content:
                clean = response.content.strip()
                if "```json" in clean:
                    clean = clean.split("```json")[1].split("```")[0].strip()
                elif "```" in clean:
                    clean = clean.split("```")[1].split("```")[0].strip()
                return json.loads(clean)
        except Exception:
            pass

        return None

    def summarize_resolution(self, prompt: str) -> Optional[str]:
        """Generate ITIL resolution note."""
        if not self.is_configured() or self.llm is None:
            return None

        try:
            messages = [
                SystemMessage(content="You are an expert ITIL documentation specialist. Generate a factual, professional resolution note."),
                HumanMessage(content=prompt),
            ]
            response = self.llm.invoke(messages)
            return response.content.strip() if response and response.content else None
        except Exception:
            return None

    def generate_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Generate structured JSON dictionary output from Gemini."""
        if not self.is_configured() or self.llm is None:
            return None

        try:
            messages = [
                SystemMessage(content="You are an enterprise AI assistant. Always output strictly valid JSON without conversational preamble or markdown codeblock wrapping."),
                HumanMessage(content=prompt),
            ]
            response = self.llm.invoke(messages)
            if response and response.content:
                clean = response.content.strip()
                if "```json" in clean:
                    clean = clean.split("```json")[1].split("```")[0].strip()
                elif "```" in clean:
                    clean = clean.split("```")[1].split("```")[0].strip()
                return json.loads(clean)
        except Exception:
            pass
        return None
