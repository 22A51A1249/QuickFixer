"""End-to-End Acceptance Tests executing the 3 required scenarios for Employee, Technician, and Admin."""

import pytest
from pathlib import Path
from src.database.db_manager import DatabaseManager
from src.models.user import UserRole
from src.models.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus
from src.auth.auth_manager import AuthManager
from src.auth.session_manager import SessionManager
from src.auth.permissions import AccessDeniedError, require_role, can_view_ticket, can_update_ticket
from src.agents.tools import create_it_ticket, generate_resolution_note, set_tool_db


@pytest.fixture
def acceptance_db(tmp_path: Path) -> DatabaseManager:
    """Isolated database for acceptance testing."""
    db_file = tmp_path / "acceptance_tickets.db"
    db = DatabaseManager(db_path=db_file)
    set_tool_db(db)
    yield db
    set_tool_db(None)


@pytest.fixture
def acceptance_auth(acceptance_db: DatabaseManager) -> AuthManager:
    """AuthManager bound to acceptance database."""
    return AuthManager(db=acceptance_db)


@pytest.fixture(autouse=True)
def clean_session():
    SessionManager.logout_user()
    yield
    SessionManager.logout_user()


def test_acceptance_workflow_1_employee(acceptance_auth: AuthManager, acceptance_db: DatabaseManager):
    """TEST 1: EMPLOYEE
    1. Employee logs in.
    2. Employee sees Employee Portal.
    3. Employee accesses AI chatbot & tools.
    4. Employee creates a ticket.
    5. Employee receives Ticket ID.
    6. Employee views their own ticket.
    7. Employee attempts to open Technician Dashboard.
    8. Application denies access.
    """
    # 1. Employee logs in
    success, employee, msg = acceptance_auth.authenticate("emp_david", "Password123!")
    assert success is True
    assert employee.role == UserRole.EMPLOYEE

    # 2. Employee authorized for employee portal
    assert require_role(["employee"], user=employee) is True

    # 3 & 4. Employee creates ticket via tool
    created_res = create_it_ticket.invoke({
        "title": "Acceptance VPN Issue",
        "description": "AnyConnect fails with error code 403 on corporate laptop.",
        "category": "Network & Connectivity",
        "priority": "High",
    })

    # 5. Receives Ticket ID
    assert "Ticket successfully created with ID: TICK-" in created_res
    import re
    ticket_id = re.search(r"TICK-\d+", created_res).group(0)

    # 6. Employee views their own ticket
    my_ticket = acceptance_db.get_ticket(ticket_id)
    assert my_ticket is not None
    assert can_view_ticket(employee, my_ticket) is True
    emp_tickets = acceptance_db.list_tickets_for_user(employee)
    assert any(t.id == ticket_id for t in emp_tickets)

    # 7 & 8. Employee attempts to open Technician Dashboard -> Denied
    with pytest.raises(AccessDeniedError):
        require_role(["technician", "admin"], user=employee)


def test_acceptance_workflow_2_technician(acceptance_auth: AuthManager, acceptance_db: DatabaseManager):
    """TEST 2: TECHNICIAN
    1. Technician logs in.
    2. Technician sees Technician Dashboard.
    3. Technician sees assigned tickets.
    4. Technician opens an assigned ticket.
    5. Technician updates ticket status.
    6. Technician generates a resolution summary.
    7. Technician attempts to open Admin Dashboard.
    8. Application denies access.
    """
    # 1. Technician logs in
    success, technician, msg = acceptance_auth.authenticate("tech_sarah", "Password123!")
    assert success is True
    assert technician.role == UserRole.TECHNICIAN

    # 2. Technician authorized for technician workspace
    assert require_role(["technician", "admin"], user=technician) is True

    # 3. Technician sees assigned tickets
    tech_tickets = acceptance_db.list_tickets_for_user(technician)
    assert len(tech_tickets) > 0

    # 4. Technician opens assigned ticket
    assigned_ticket = tech_tickets[0]
    assert can_view_ticket(technician, assigned_ticket) is True
    assert can_update_ticket(technician, assigned_ticket) is True

    # 5. Technician updates ticket status
    update_ok = acceptance_db.update_status(
        ticket_id=assigned_ticket.id,
        new_status=TicketStatus.RESOLVED,
        assigned_to=technician.full_name,
        resolution_notes="Remediated DNS configuration on router.",
    )
    assert update_ok is True

    # 6. Technician generates resolution summary
    summary_note = generate_resolution_note.invoke({"ticket_id": assigned_ticket.id})
    assert f"ITIL Resolution Note for {assigned_ticket.id}" in summary_note
    assert "Access Denied" not in summary_note

    # 7 & 8. Technician attempts to open Admin Dashboard -> Denied
    with pytest.raises(AccessDeniedError):
        require_role(["admin"], user=technician)


def test_acceptance_workflow_3_admin(acceptance_auth: AuthManager, acceptance_db: DatabaseManager):
    """TEST 3: ADMIN
    1. Admin logs in.
    2. Admin sees Admin Dashboard.
    3. Admin creates an employee.
    4. Admin creates a technician.
    5. Admin assigns a ticket.
    6. Admin views all tickets.
    7. Admin manages user roles.
    """
    # 1. Admin logs in
    success, admin, msg = acceptance_auth.authenticate("admin", "ApexAdmin2026!")
    assert success is True
    assert admin.role == UserRole.ADMIN

    # 2. Admin authorized for admin dashboard
    assert require_role(["admin"], user=admin) is True

    # 3. Admin creates an employee
    ok_emp, new_emp, _ = acceptance_auth.create_user(
        username="emp_bruce",
        email="bruce.wayne@company.com",
        full_name="Bruce Wayne",
        password="SecurePass2026!",
        role=UserRole.EMPLOYEE,
        created_by=admin,
    )
    assert ok_emp is True
    assert new_emp.role == UserRole.EMPLOYEE

    # 4. Admin creates a technician
    ok_tech, new_tech, _ = acceptance_auth.create_user(
        username="tech_lucius",
        email="lucius.fox@company.com",
        full_name="Lucius Fox",
        password="SecurePass2026!",
        role=UserRole.TECHNICIAN,
        team="Deskside & Hardware Support",
        created_by=admin,
    )
    assert ok_tech is True
    assert new_tech.role == UserRole.TECHNICIAN

    # 5. Admin assigns a ticket
    assign_ok = acceptance_db.assign_ticket("TICK-1001", "Lucius Fox (Technician)")
    assert assign_ok is True
    updated_ticket = acceptance_db.get_ticket("TICK-1001")
    assert updated_ticket.assigned_to == "Lucius Fox (Technician)"

    # 6. Admin views all tickets
    all_tickets = acceptance_db.list_tickets_for_user(admin)
    assert len(all_tickets) >= 5

    # 7. Admin manages user roles (promotes Bruce Wayne to Technician)
    role_ok = acceptance_auth.update_user_role(
        user_id=new_emp.id,
        new_role=UserRole.TECHNICIAN,
        team="Security Operations Center (SOC)",
        performed_by=admin,
    )
    assert role_ok is True
    refreshed_emp = acceptance_db.get_user_by_id(new_emp.id)
    assert refreshed_emp.role == UserRole.TECHNICIAN
    assert refreshed_emp.team == "Security Operations Center (SOC)"
