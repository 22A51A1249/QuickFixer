"""Dashboard and system analytics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from src.database.db_manager import DatabaseManager
from src.models.user import User, UserRole
from backend.dependencies import get_db, get_current_user
from backend.schemas.dashboard import DashboardStatsResponse

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard Analytics"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Retrieve service desk statistics and distribution metrics computed directly from SQLite."""
    base_stats = db.get_stats()
    all_users = db.list_users()

    total_employees = sum(1 for u in all_users if u.role == UserRole.EMPLOYEE)
    total_technicians = sum(1 for u in all_users if u.role == UserRole.TECHNICIAN)

    # Compute status distribution and team distribution directly
    all_tickets = db.list_tickets()
    status_dist = {}
    team_dist = {}
    critical_count = 0

    for t in all_tickets:
        s_val = t.status.value if hasattr(t.status, "value") else str(t.status)
        status_dist[s_val] = status_dist.get(s_val, 0) + 1

        team = t.assigned_to or "Unassigned"
        team_dist[team] = team_dist.get(team, 0) + 1

        p_val = t.priority.value if hasattr(t.priority, "value") else str(t.priority)
        if p_val.lower() == "critical" and s_val.lower() in ("open", "in progress"):
            critical_count += 1

    return DashboardStatsResponse(
        total_tickets=base_stats["total_tickets"],
        open_tickets=base_stats["open_tickets"],
        in_progress_tickets=base_stats["in_progress_tickets"],
        resolved_tickets=base_stats["resolved_tickets"],
        resolution_rate=base_stats["resolution_rate"],
        avg_rating=base_stats["avg_rating"],
        priority_distribution=base_stats.get("priority_distribution", {}),
        category_distribution=base_stats.get("category_distribution", {}),
        status_distribution=status_dist,
        team_distribution=team_dist,
        total_employees=total_employees,
        total_technicians=total_technicians,
        critical_tickets=critical_count,
    )

