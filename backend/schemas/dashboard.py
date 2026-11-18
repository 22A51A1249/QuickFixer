"""Dashboard analytics and statistics schemas."""

from __future__ import annotations
from typing import Dict, Any, List
from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    resolution_rate: float
    avg_rating: float
    priority_distribution: Dict[str, int]
    category_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    team_distribution: Dict[str, int]
    total_employees: int
    total_technicians: int
    critical_tickets: int

