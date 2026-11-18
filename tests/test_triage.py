"""Unit tests for Triage Classification, Priority Detection, and Offline Engine."""

from src.models.ticket import TicketCategory, TicketPriority
from src.llm.offline_engine import OfflineDiagnosticEngine
from src.rag.document_loader import DocumentChunk


def test_triage_network_category():
    engine = OfflineDiagnosticEngine()
    result = engine.triage_description("Cisco AnyConnect VPN connection fails with gateway timeout.")
    assert result.category == TicketCategory.NETWORK
    assert len(result.immediate_actions) > 0


def test_triage_password_and_account():
    engine = OfflineDiagnosticEngine()
    result = engine.triage_description("Locked out of my laptop after MFA authenticator failed.")
    assert result.category == TicketCategory.ACCOUNT
    assert result.priority in (TicketPriority.HIGH, TicketPriority.CRITICAL)


def test_triage_critical_priority():
    engine = OfflineDiagnosticEngine()
    result = engine.triage_description(
        "Company wide outage: production database is down and nobody can login emergency."
    )
    assert result.priority == TicketPriority.CRITICAL


def test_triage_low_priority():
    engine = OfflineDiagnosticEngine()
    result = engine.triage_description("How do i request access to Docker desktop when possible?")
    assert result.priority == TicketPriority.LOW


def test_offline_response_synthesis():
    engine = OfflineDiagnosticEngine()
    chunk = DocumentChunk(
        doc_id="c1",
        source="vpn.md",
        title="VPN Troubleshooting",
        text="To resolve VPN drops:\n1. Flush DNS cache via ipconfig /flushdns\n2. Reconnect adapter.",
        chunk_index=0,
    )
    response = engine.synthesize_response("VPN connection failed", [(chunk, 0.92)])
    assert "VPN Troubleshooting" in response
    assert "ipconfig /flushdns" in response

