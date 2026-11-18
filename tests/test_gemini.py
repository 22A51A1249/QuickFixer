"""Unit tests for Google Gemini client and fallback mechanics."""

import pytest
from src.llm.gemini_client import GeminiClient
from config import settings


def test_gemini_client_init_and_config():
    """Verify Gemini client initialization, settings defaults, and configuration check."""
    client = GeminiClient(api_key="", model_name="gemini-2.0-flash")
    assert client.model_name == "gemini-2.0-flash"
    assert client.is_configured() is False


def test_gemini_client_update_key():
    """Verify updating API key configures LLM without crashing."""
    client = GeminiClient(api_key="")
    assert client.is_configured() is False

    # Empty key resets client
    success = client.update_key("")
    assert success is False
    assert client.is_configured() is False


def test_gemini_offline_graceful_fallback():
    """Verify that unconfigured Gemini client returns None gracefully instead of raising exceptions."""
    client = GeminiClient(api_key="")

    res = client.generate_response(
        user_message="Test prompt",
        conversation_history=[],
        rag_context="Test context",
    )
    assert res is None

    triage = client.triage_ticket("VPN connection fails")
    assert triage is None

    summary = client.summarize_resolution("Resolution prompt")
    assert summary is None

    intent = client.classify_query_intent("Check ticket TICK-1001")
    assert intent is None

