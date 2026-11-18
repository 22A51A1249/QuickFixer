"""Integration tests for QuickFixer FastAPI REST API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_system_health():
    """Verify system health endpoint reports database and vector store status."""
    res = client.get("/api/system/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "QuickFixer"
    assert "vector_store" in data
    assert "database" in data


def test_auth_login_and_me():
    """Verify authentication for admin, technician, and employee roles."""
    # 1. Admin login
    res_admin = client.post(
        "/api/auth/login",
        json={"username_or_email": "admin", "password": "ApexAdmin2026!"},
    )
    assert res_admin.status_code == 200
    admin_data = res_admin.json()
    assert "token" in admin_data
    assert admin_data["user"]["role"] == "admin"
    admin_token = admin_data["token"]

    # Test /api/auth/me with admin token
    res_me = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_me.status_code == 200
    assert res_me.json()["username"] == "admin"

    # 2. Employee login
    res_emp = client.post(
        "/api/auth/login",
        json={"username_or_email": "emp_david", "password": "Password123!"},
    )
    assert res_emp.status_code == 200
    emp_data = res_emp.json()
    assert emp_data["user"]["role"] == "employee"

    # 3. Technician login
    res_tech = client.post(
        "/api/auth/login",
        json={"username_or_email": "tech_sarah", "password": "Password123!"},
    )
    assert res_tech.status_code == 200
    tech_data = res_tech.json()
    assert tech_data["user"]["role"] == "technician"

    # 4. Invalid credentials
    res_invalid = client.post(
        "/api/auth/login",
        json={"username_or_email": "admin", "password": "WrongPassword999!"},
    )
    assert res_invalid.status_code == 401


def test_rbac_endpoint_protection():
    """Ensure employee cannot access admin or unauthorized endpoints."""
    # Employee login
    res_emp = client.post(
        "/api/auth/login",
        json={"username_or_email": "emp_david", "password": "Password123!"},
    )
    emp_token = res_emp.json()["token"]
    emp_headers = {"Authorization": f"Bearer {emp_token}"}

    # Employee tries to list admin users -> 403 Forbidden
    res_admin_users = client.get("/api/admin/users", headers=emp_headers)
    assert res_admin_users.status_code == 403

    # Employee tries to access audit logs -> 403 Forbidden
    res_audit = client.get("/api/admin/audit-logs", headers=emp_headers)
    assert res_audit.status_code == 403

    # Employee tries to re-index knowledge base -> 403 Forbidden
    res_reindex = client.post("/api/knowledge/reindex", headers=emp_headers)
    assert res_reindex.status_code == 403


def test_ai_chat_out_of_scope_guardrail():
    """Verify that 'pm of india' or general trivia is caught by domain guardrail in API."""
    res_emp = client.post(
        "/api/auth/login",
        json={"username_or_email": "emp_david", "password": "Password123!"},
    )
    emp_token = res_emp.json()["token"]

    res_chat = client.post(
        "/api/chat/message",
        json={"message": "pm of india"},
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert res_chat.status_code == 200
    chat_data = res_chat.json()
    # Expect out of scope response
    assert chat_data["query_type"] == "out_of_scope"
    assert (
        "does not appear to be related to IT support" in chat_data["answer"]
        or "IT problem" in chat_data["answer"]
    )


def test_ai_chat_hardware_shutdown_handling():
    """Verify that unexpected shutdown inquiry receives relevant diagnosis, not VPN or printer."""
    res_emp = client.post(
        "/api/auth/login",
        json={"username_or_email": "emp_david", "password": "Password123!"},
    )
    emp_token = res_emp.json()["token"]

    res_chat = client.post(
        "/api/chat/message",
        json={"message": "My system suddenly froze and switched off."},
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert res_chat.status_code == 200
    chat_data = res_chat.json()
    answer_lower = chat_data["answer"].lower()
    # Must relate to power / shutdown / crash, NOT vpn or printer
    assert "vpn" not in answer_lower or "anyconnect" not in answer_lower
    assert "printer" not in answer_lower


def test_ticket_lifecycle_and_scoped_access():
    """Verify ticket creation, scoped listing, and technician status update."""
    # 1. Employee submits a ticket
    res_emp = client.post(
        "/api/auth/login",
        json={"username_or_email": "emp_david", "password": "Password123!"},
    )
    emp_token = res_emp.json()["token"]
    emp_headers = {"Authorization": f"Bearer {emp_token}"}

    create_res = client.post(
        "/api/tickets",
        json={
            "title": "VPN connection drops every 5 minutes",
            "description": "My corporate Cisco AnyConnect VPN client disconnects repeatedly with error 404.",
            "device_info": "Windows 11 Enterprise",
        },
        headers=emp_headers,
    )
    assert create_res.status_code == 201
    ticket = create_res.json()
    ticket_id = ticket["id"]
    assert ticket_id.startswith("TICK-")
    assert ticket["status"] == "Open"

    # 2. Employee lists tickets -> sees their own ticket
    list_res = client.get("/api/tickets", headers=emp_headers)
    assert list_res.status_code == 200
    emp_ticket_ids = [t["id"] for t in list_res.json()]
    assert ticket_id in emp_ticket_ids

    # 3. Technician updates status to "In Progress"
    res_tech = client.post(
        "/api/auth/login",
        json={"username_or_email": "tech_sarah", "password": "Password123!"},
    )
    tech_token = res_tech.json()["token"]
    tech_headers = {"Authorization": f"Bearer {tech_token}"}

    update_res = client.patch(
        f"/api/tickets/{ticket_id}/status",
        json={"status": "In Progress", "resolution_notes": "Investigating MTU packet sizing."},
        headers=tech_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "In Progress"

    # 4. Add message to ticket
    msg_res = client.post(
        f"/api/tickets/{ticket_id}/messages",
        json={"message": "Please confirm if your home Wi-Fi MTU is set to 1500."},
        headers=tech_headers,
    )
    assert msg_res.status_code == 200
    assert msg_res.json()["ticket_id"] == ticket_id


def test_dashboard_and_knowledge_endpoints():
    """Verify dashboard stats and knowledge base endpoints."""
    # Admin login
    res_admin = client.post(
        "/api/auth/login",
        json={"username_or_email": "admin", "password": "ApexAdmin2026!"},
    )
    admin_token = res_admin.json()["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Dashboard stats
    stats_res = client.get("/api/dashboard/stats", headers=admin_headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "total_tickets" in stats
    assert "priority_distribution" in stats
    assert "status_distribution" in stats

    # Knowledge base documents
    kb_res = client.get("/api/knowledge/documents", headers=admin_headers)
    assert kb_res.status_code == 200
    docs = kb_res.json()
    assert len(docs) > 0
    assert any("vpn" in d["filename"].lower() for d in docs)


def test_frontend_spa_serving():
    """Verify that FastAPI serves the compiled React single page application."""
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "QuickFixer" in res_root.text

    res_login_route = client.get("/login")
    assert res_login_route.status_code == 200
    assert "QuickFixer" in res_login_route.text

