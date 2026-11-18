"""Unit and security integration tests for ApexIT Authentication and RBAC."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from src.database.db_manager import DatabaseManager
from src.models.user import User, UserRole
from src.models.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus
from src.auth.password_manager import PasswordManager
from src.auth.session_manager import SessionManager
from src.auth.auth_manager import AuthManager
from src.auth.permissions import (
    AccessDeniedError,
    require_login,
    require_role,
    can_view_ticket,
    can_update_ticket,
    can_assign_ticket,
    can_manage_users,
)
from src.agents.tools import (
    get_ticket_status,
    get_employee_ticket_history,
    generate_resolution_note,
)


@pytest.fixture
def test_db(tmp_path: Path) -> DatabaseManager:
    """Provide an isolated, freshly initialized SQLite database for testing."""
    db_file = tmp_path / "test_rbac.db"
    manager = DatabaseManager(db_path=db_file)
    return manager


@pytest.fixture
def auth_mgr(test_db: DatabaseManager) -> AuthManager:
    """Provide an AuthManager bound to the isolated test database."""
    return AuthManager(db=test_db)


@pytest.fixture(autouse=True)
def clean_session():
    """Ensure session state is clean before and after every test."""
    SessionManager.logout_user()
    yield
    SessionManager.logout_user()


# -------------------------------------------------------------------------
# 1. LOGIN TESTS FOR ALL 3 ROLES
# -------------------------------------------------------------------------

def test_employee_login(auth_mgr: AuthManager):
    """Verify employee can authenticate successfully."""
    success, user, msg = auth_mgr.authenticate("emp_david", "Password123!")
    assert success is True
    assert user is not None
    assert user.role == UserRole.EMPLOYEE
    assert user.username == "emp_david"
    assert SessionManager.is_authenticated() is True


def test_technician_login(auth_mgr: AuthManager):
    """Verify technician can authenticate successfully."""
    success, user, msg = auth_mgr.authenticate("tech_sarah", "Password123!")
    assert success is True
    assert user is not None
    assert user.role == UserRole.TECHNICIAN
    assert "NetOps" in user.team
    assert SessionManager.is_authenticated() is True


def test_admin_login(auth_mgr: AuthManager):
    """Verify administrator can authenticate successfully."""
    success, user, msg = auth_mgr.authenticate("admin", "ApexAdmin2026!")
    assert success is True
    assert user is not None
    assert user.role == UserRole.ADMIN
    assert user.is_admin is True
    assert SessionManager.is_authenticated() is True


# -------------------------------------------------------------------------
# 2. CREDENTIAL & ACCOUNT STATUS VALIDATION
# -------------------------------------------------------------------------

def test_invalid_credentials_unknown_user(auth_mgr: AuthManager):
    """Verify authentication fails for nonexistent username."""
    success, user, msg = auth_mgr.authenticate("nonexistent_user", "SomePassword123!")
    assert success is False
    assert user is None
    assert "Invalid credentials" in msg
    assert SessionManager.is_authenticated() is False


def test_incorrect_password(auth_mgr: AuthManager):
    """Verify authentication fails when wrong password is supplied."""
    success, user, msg = auth_mgr.authenticate("emp_david", "WrongPassword999!")
    assert success is False
    assert user is None
    assert "Invalid credentials" in msg
    assert SessionManager.is_authenticated() is False


def test_inactive_account_denied(auth_mgr: AuthManager, test_db: DatabaseManager):
    """Verify deactivated user accounts cannot log in."""
    user, _ = test_db.get_user_by_username("emp_alice")
    test_db.update_user_status(user.id, is_active=False)

    success, authenticated_user, msg = auth_mgr.authenticate("emp_alice", "Password123!")
    assert success is False
    assert authenticated_user is None
    assert "deactivated" in msg.lower()
    assert SessionManager.is_authenticated() is False


# -------------------------------------------------------------------------
# 3. RBAC ACCESS DENIAL TESTS
# -------------------------------------------------------------------------

def test_employee_denied_technician_access():
    """Verify employee is denied access when requiring technician role."""
    emp = User(
        id="u-1",
        username="emp_user",
        email="emp@company.com",
        full_name="Employee User",
        role=UserRole.EMPLOYEE,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )
    SessionManager.login_user(emp)

    with pytest.raises(AccessDeniedError):
        require_role(["technician", "admin"])


def test_employee_denied_admin_access():
    """Verify employee is denied access when requiring admin role."""
    emp = User(
        id="u-1",
        username="emp_user",
        email="emp@company.com",
        full_name="Employee User",
        role=UserRole.EMPLOYEE,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )
    SessionManager.login_user(emp)

    with pytest.raises(AccessDeniedError):
        require_role(["admin"])


def test_technician_denied_admin_access():
    """Verify technician is denied access when requiring admin role."""
    tech = User(
        id="u-2",
        username="tech_user",
        email="tech@company.com",
        full_name="Technician User",
        role=UserRole.TECHNICIAN,
        team="NetOps",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )
    SessionManager.login_user(tech)

    with pytest.raises(AccessDeniedError):
        require_role(["admin"])


# -------------------------------------------------------------------------
# 4. TICKET-LEVEL OWNERSHIP & AUTHORIZATION
# -------------------------------------------------------------------------

def test_employee_cannot_view_another_employee_ticket():
    """Verify employee cannot view tickets submitted by a different employee."""
    emp_alice = User(
        id="u-alice",
        username="emp_alice",
        email="alice@company.com",
        full_name="Alice Smith",
        role=UserRole.EMPLOYEE,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )

    other_ticket = Ticket(
        id="TICK-1001",
        title="VPN Timeout",
        description="Issue",
        category=TicketCategory.NETWORK,
        priority=TicketPriority.HIGH,
        status=TicketStatus.OPEN,
        user_name="David Miller",
        user_email="dmiller@company.com",
    )

    assert can_view_ticket(emp_alice, other_ticket) is False


def test_employee_can_view_own_ticket():
    """Verify employee can view their own ticket."""
    emp_alice = User(
        id="u-alice",
        username="emp_alice",
        email="alice@company.com",
        full_name="Alice Smith",
        role=UserRole.EMPLOYEE,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )

    own_ticket = Ticket(
        id="TICK-1002",
        title="MFA Failure",
        description="Issue",
        category=TicketCategory.ACCOUNT,
        priority=TicketPriority.MEDIUM,
        status=TicketStatus.OPEN,
        user_name="Alice Smith",
        user_email="alice@company.com",
    )

    assert can_view_ticket(emp_alice, own_ticket) is True


def test_technician_authorization_scopes():
    """Verify technician can view assigned/team tickets but not unauthorized queues."""
    tech_netops = User(
        id="u-tech-1",
        username="tech_sarah",
        email="sarah@company.com",
        full_name="Sarah Connor",
        role=UserRole.TECHNICIAN,
        team="NetOps & Network Infrastructure",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )

    # Authorized team ticket
    netops_ticket = Ticket(
        id="TICK-1001",
        title="Router Failure",
        description="Switch offline",
        category=TicketCategory.NETWORK,
        priority=TicketPriority.CRITICAL,
        status=TicketStatus.OPEN,
        assigned_to="NetOps & Network Infrastructure",
    )
    assert can_view_ticket(tech_netops, netops_ticket) is True
    assert can_update_ticket(tech_netops, netops_ticket) is True

    # Unauthorized hardware ticket assigned specifically to someone else
    hw_ticket = Ticket(
        id="TICK-1005",
        title="Printer Drum Stuck",
        description="Printer broken",
        category=TicketCategory.HARDWARE,
        priority=TicketPriority.LOW,
        status=TicketStatus.OPEN,
        assigned_to="Mike Ross (Deskside & Hardware Support)",
    )
    assert can_view_ticket(tech_netops, hw_ticket) is False
    assert can_update_ticket(tech_netops, hw_ticket) is False


def test_admin_has_universal_access():
    """Verify administrator has universal view, update, assign, and manage rights."""
    admin = User(
        id="u-admin",
        username="admin",
        email="admin@company.com",
        full_name="System Admin",
        role=UserRole.ADMIN,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )

    any_ticket = Ticket(
        id="TICK-9999",
        title="Any Incident",
        description="Random issue",
        category=TicketCategory.OTHER,
        priority=TicketPriority.LOW,
        status=TicketStatus.OPEN,
        assigned_to="Exclusive Queue",
    )

    assert can_view_ticket(admin, any_ticket) is True
    assert can_update_ticket(admin, any_ticket) is True
    assert can_assign_ticket(admin, any_ticket) is True
    assert can_manage_users(admin) is True


# -------------------------------------------------------------------------
# 5. USER LIFECYCLE & ROLE CHANGES
# -------------------------------------------------------------------------

def test_admin_can_manage_users(auth_mgr: AuthManager, test_db: DatabaseManager):
    """Verify administrator can create, deactivate, and promote users."""
    admin, _ = test_db.get_user_by_username("admin")
    SessionManager.login_user(admin)

    # 1. Create a technician
    success, new_tech, msg = auth_mgr.create_user(
        username="tech_kevin",
        email="kevin@company.com",
        full_name="Kevin Flynn",
        password="SecurePass2026!",
        role=UserRole.TECHNICIAN,
        team="Security Operations Center (SOC)",
        created_by=admin,
    )
    assert success is True
    assert new_tech.role == UserRole.TECHNICIAN

    # 2. Promote to Admin
    auth_mgr.update_user_role(new_tech.id, UserRole.ADMIN, performed_by=admin)
    updated_user = test_db.get_user_by_id(new_tech.id)
    assert updated_user.role == UserRole.ADMIN

    # 3. Deactivate user
    auth_mgr.update_user_status(new_tech.id, is_active=False, performed_by=admin)
    deactivated = test_db.get_user_by_id(new_tech.id)
    assert deactivated.is_active is False


# -------------------------------------------------------------------------
# 6. SESSION MANAGEMENT & LOGOUT
# -------------------------------------------------------------------------

def test_logout_clears_session():
    """Verify logout terminates session and invalidates access."""
    user = User(
        id="u-test",
        username="test_user",
        email="test@company.com",
        full_name="Test User",
        role=UserRole.EMPLOYEE,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )
    SessionManager.login_user(user)
    assert SessionManager.is_authenticated() is True

    SessionManager.logout_user()
    assert SessionManager.is_authenticated() is False
    assert SessionManager.get_current_user() is None


def test_session_inactivity_expiration(monkeypatch):
    """Verify session expires after configured inactivity timeout."""
    user = User(
        id="u-test",
        username="test_user",
        email="test@company.com",
        full_name="Test User",
        role=UserRole.EMPLOYEE,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )
    SessionManager.login_user(user)

    # Simulate expired last activity
    expired_time = (datetime.now() - timedelta(minutes=70)).isoformat()
    session_data = SessionManager.get_session_data()
    session_data["last_activity"] = expired_time

    # Accessing session now should trigger expiration
    active_user = SessionManager.get_current_user()
    assert active_user is None
    assert SessionManager.is_authenticated() is False


# -------------------------------------------------------------------------
# 7. LANGGRAPH & LANGCHAIN TOOL AUTHORIZATION
# -------------------------------------------------------------------------

def test_unauthorized_tool_execution():
    """Verify that employee cannot execute technician resolution tools or view other employees' tickets."""
    emp = User(
        id="u-emp-1",
        username="emp_david",
        email="dmiller@company.com",
        full_name="David Miller",
        role=UserRole.EMPLOYEE,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )
    SessionManager.login_user(emp)

    # 1. Employee denied generating resolution note
    res_note = generate_resolution_note.invoke({"ticket_id": "TICK-1001"})
    assert "Access Denied" in res_note

    # 2. Employee denied querying another employee's ticket history
    history_res = get_employee_ticket_history.invoke({"user_email": "sarah.connor@example.com"})
    assert "Access Denied" in history_res

    # 3. Employee can query their own history
    own_history = get_employee_ticket_history.invoke({"user_email": "dmiller@company.com"})
    assert "Access Denied" not in own_history

