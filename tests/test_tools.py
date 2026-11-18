"""Unit tests for LangChain Tools in ApexIT."""

import pytest
from src.agents.tools import (
    search_knowledge_base,
    search_runbook,
    create_it_ticket,
    get_ticket_status,
    get_employee_ticket_history,
    generate_resolution_note,
)


def test_tool_search_knowledge_base():
    """Verify semantic search tool returns formatted knowledge chunks."""
    output = search_knowledge_base.invoke({"query": "VPN connection drops"})
    assert isinstance(output, str)
    assert len(output) > 0
    assert "Match:" in output or "runbooks found" in output


def test_tool_search_runbook():
    """Verify specific runbook retrieval tool."""
    output = search_runbook.invoke({"issue": "printer offline"})
    assert isinstance(output, str)
    assert "Runbook:" in output or "printer" in output.lower()


def test_tool_create_it_ticket():
    """Verify tool creating an IT ticket and duplicate detection."""
    import uuid

    unique_title = f"Tool Test Incident - Monitor Glitch {uuid.uuid4().hex[:6]}"
    result = create_it_ticket.invoke(
        {
            "title": unique_title,
            "description": "External monitor flashes black intermittently via HDMI cable.",
            "category": "Hardware & Peripherals",
            "priority": "Medium",
            "assigned_team": "Hardware Support",
            "user_name": "Dev User",
            "user_email": "dev.user@company.com",
        }
    )
    assert "Ticket successfully created with ID: TICK-" in result

    # Test duplicate detection
    duplicate_result = create_it_ticket.invoke(
        {
            "title": unique_title,
            "description": "External monitor flashes black intermittently via HDMI cable.",
            "category": "Hardware & Peripherals",
            "priority": "Medium",
            "assigned_team": "Hardware Support",
            "user_name": "Dev User",
            "user_email": "dev.user@company.com",
        }
    )
    assert "Duplicate ticket detected" in duplicate_result


def test_tool_get_ticket_status():
    """Verify ticket status lookup for existing and missing tickets."""
    # Existing ticket
    status_output = get_ticket_status.invoke({"ticket_id": "TICK-1001"})
    assert "Ticket ID: TICK-1001" in status_output
    assert "Status:" in status_output
    assert "Priority:" in status_output

    # Missing ticket
    missing_output = get_ticket_status.invoke({"ticket_id": "TICK-99999"})
    assert "was not found" in missing_output


def test_tool_get_employee_ticket_history():
    """Verify employee ticket history lookup with email validation."""
    # Invalid email
    invalid_out = get_employee_ticket_history.invoke({"user_email": "invalid_email_format"})
    assert "Invalid email address format" in invalid_out

    # Valid lookup (may find 0 or more tickets depending on seeded user)
    valid_out = get_employee_ticket_history.invoke({"user_email": "sarah.connor@example.com"})
    assert "sarah.connor@example.com" in valid_out


def test_tool_generate_resolution_note():
    """Verify drafting ITIL resolution note from ticket audit history."""
    note_output = generate_resolution_note.invoke({"ticket_id": "TICK-1001"})
    assert "ITIL Resolution Note for TICK-1001" in note_output
    assert "Root Cause:" in note_output
    assert "Audit History summary:" in note_output

