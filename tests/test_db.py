"""Unit tests for SQLite database management and ticket operations."""

import pytest
from pathlib import Path
from src.database.db_manager import DatabaseManager
from src.models.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus, TicketMessage


@pytest.fixture
def test_db(tmp_path: Path):
    db_file = tmp_path / "test_tickets.db"
    manager = DatabaseManager(db_path=db_file)
    return manager


def test_init_and_seed(test_db: DatabaseManager):
    tickets = test_db.list_tickets()
    assert len(tickets) >= 5
    assert any(t.category == TicketCategory.NETWORK for t in tickets)


def test_create_and_get_ticket(test_db: DatabaseManager):
    new_ticket = Ticket(
        id="",
        title="Test Monitor Flicker",
        description="Monitor flickers every 5 seconds on USB-C dock",
        category=TicketCategory.HARDWARE,
        priority=TicketPriority.MEDIUM,
        user_name="John Doe",
        user_email="jdoe@example.com",
    )
    created = test_db.create_ticket(new_ticket)
    assert created.id.startswith("TICK-")

    retrieved = test_db.get_ticket(created.id)
    assert retrieved is not None
    assert retrieved.title == "Test Monitor Flicker"
    assert retrieved.category == TicketCategory.HARDWARE


def test_update_ticket_status(test_db: DatabaseManager):
    tickets = test_db.list_tickets()
    first_ticket = tickets[0]

    success = test_db.update_status(
        ticket_id=first_ticket.id,
        new_status=TicketStatus.RESOLVED,
        assigned_to="Lead Engineer",
        resolution_notes="Fixed adapter driver issue.",
    )
    assert success is True

    updated = test_db.get_ticket(first_ticket.id)
    assert updated.status == TicketStatus.RESOLVED
    assert updated.assigned_to == "Lead Engineer"
    assert updated.resolution_notes == "Fixed adapter driver issue."


def test_ticket_messages(test_db: DatabaseManager):
    tickets = test_db.list_tickets()
    ticket_id = tickets[0].id

    test_db.add_message(
        TicketMessage(
            ticket_id=ticket_id,
            sender="technician",
            message="Please reboot your laptop and verify.",
        )
    )

    messages = test_db.get_messages(ticket_id)
    assert len(messages) >= 2
    assert any("reboot your laptop" in m.message for m in messages)

def test_get_stats(test_db: DatabaseManager):
    stats = test_db.get_stats()
    assert "total_tickets" in stats
    assert stats["total_tickets"] >= 5
    assert "resolution_rate" in stats
    assert "priority_distribution" in stats

