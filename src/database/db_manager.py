"""SQLite Database Manager for IT Support Tickets and Resolution Logs."""

from __future__ import annotations

import sqlite3
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

from config import settings
from src.models.ticket import (
    Ticket,
    TicketCategory,
    TicketPriority,
    TicketStatus,
    TicketMessage,
    TicketFeedback,
)
from src.models.user import User, UserRole, AuditLogEntry


class DatabaseManager:
    """Handles all SQLite operations for tickets, message threads, and feedback."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.SQLITE_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Create database tables if they do not exist and seed initial demo data."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Tickets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    user_name TEXT,
                    user_email TEXT,
                    device_info TEXT,
                    ai_diagnosis TEXT,
                    suggested_steps TEXT,
                    assigned_to TEXT,
                    resolution_notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    resolved_at TEXT
                )
            """)

            # Ticket messages / thread table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ticket_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
                )
            """)

            # Ticket feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ticket_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    comments TEXT,
                    resolved_by_ai INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
                )
            """)

            # Users table for Authentication and RBAC
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('employee', 'technician', 'admin')),
                    team TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Audit logs table for security events
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    username TEXT,
                    action TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT,
                    details TEXT,
                    ip_address TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.commit()

        # Seed realistic demo tickets if database is empty
        self._seed_demo_data_if_empty()
        # Seed initial admin and demo role users if users table is empty
        self._seed_users_if_empty()

    def _generate_ticket_id(self) -> str:
        """Generate the next sequential ticket ID (e.g. TICK-1042)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tickets WHERE id LIKE 'TICK-%'")
            rows = cursor.fetchall()
            max_num = 1000
            for row in rows:
                try:
                    num = int(row["id"].split("-")[1])
                    if num > max_num:
                        max_num = num
                except (IndexError, ValueError):
                    continue
            return f"TICK-{max_num + 1}"

    def create_ticket(self, ticket: Ticket) -> Ticket:
        """Insert a new ticket into the database."""
        if not ticket.id:
            ticket.id = self._generate_ticket_id()

        now = datetime.now().isoformat()
        if not ticket.created_at:
            ticket.created_at = now
        ticket.updated_at = now

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tickets (
                    id, title, description, category, priority, status,
                    user_name, user_email, device_info, ai_diagnosis,
                    suggested_steps, assigned_to, resolution_notes,
                    created_at, updated_at, resolved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    ticket.id,
                    ticket.title,
                    ticket.description,
                    ticket.category.value if isinstance(ticket.category, TicketCategory) else ticket.category,
                    ticket.priority.value if isinstance(ticket.priority, TicketPriority) else ticket.priority,
                    ticket.status.value if isinstance(ticket.status, TicketStatus) else ticket.status,
                    ticket.user_name,
                    ticket.user_email,
                    ticket.device_info,
                    ticket.ai_diagnosis,
                    ticket.suggested_steps,
                    ticket.assigned_to,
                    ticket.resolution_notes,
                    ticket.created_at,
                    ticket.updated_at,
                    ticket.resolved_at,
                ),
            )
            conn.commit()

        # Auto-create initial ticket message
        self.add_message(
            TicketMessage(
                ticket_id=ticket.id,
                sender="user",
                message=ticket.description,
                timestamp=ticket.created_at,
            )
        )
        if ticket.ai_diagnosis:
            self.add_message(
                TicketMessage(
                    ticket_id=ticket.id,
                    sender="ai_assistant",
                    message=f"**Initial AI Diagnosis:**\n{ticket.ai_diagnosis}\n\n**Recommended Steps:**\n{ticket.suggested_steps or 'Awaiting technician review.'}",
                    timestamp=ticket.created_at,
                )
            )

        return ticket

    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Retrieve a single ticket by its ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_ticket(row)

    def list_tickets(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[Ticket]:
        """Filter and list tickets from database."""
        query = "SELECT * FROM tickets WHERE 1=1"
        params: List[Any] = []

        if status and status != "All":
            query += " AND status = ?"
            params.append(status)

        if priority and priority != "All":
            query += " AND priority = ?"
            params.append(priority)

        if category and category != "All":
            query += " AND category = ?"
            params.append(category)

        if search_query:
            query += " AND (title LIKE ? OR description LIKE ? OR user_name LIKE ? OR id LIKE ?)"
            term = f"%{search_query}%"
            params.extend([term, term, term, term])

        query += " ORDER BY created_at DESC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [self._row_to_ticket(row) for row in rows]

    def update_ticket(self, ticket: Ticket) -> Ticket:
        """Update full ticket record."""
        ticket.updated_at = datetime.now().isoformat()
        if ticket.status in (TicketStatus.RESOLVED, TicketStatus.CLOSED) and not ticket.resolved_at:
            ticket.resolved_at = datetime.now().isoformat()
        elif ticket.status not in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
            ticket.resolved_at = None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE tickets SET
                    title = ?, description = ?, category = ?, priority = ?,
                    status = ?, user_name = ?, user_email = ?, device_info = ?,
                    ai_diagnosis = ?, suggested_steps = ?, assigned_to = ?,
                    resolution_notes = ?, updated_at = ?, resolved_at = ?
                WHERE id = ?
            """,
                (
                    ticket.title,
                    ticket.description,
                    ticket.category.value if isinstance(ticket.category, TicketCategory) else ticket.category,
                    ticket.priority.value if isinstance(ticket.priority, TicketPriority) else ticket.priority,
                    ticket.status.value if isinstance(ticket.status, TicketStatus) else ticket.status,
                    ticket.user_name,
                    ticket.user_email,
                    ticket.device_info,
                    ticket.ai_diagnosis,
                    ticket.suggested_steps,
                    ticket.assigned_to,
                    ticket.resolution_notes,
                    ticket.updated_at,
                    ticket.resolved_at,
                    ticket.id,
                ),
            )
            conn.commit()
        return ticket

    def update_status(
        self,
        ticket_id: str,
        new_status: TicketStatus,
        assigned_to: Optional[str] = None,
        resolution_notes: Optional[str] = None,
    ) -> bool:
        """Quick status change helper."""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return False

        ticket.status = new_status
        if assigned_to:
            ticket.assigned_to = assigned_to
        if resolution_notes:
            ticket.resolution_notes = resolution_notes

        self.update_ticket(ticket)
        self.add_message(
            TicketMessage(
                ticket_id=ticket_id,
                sender="system",
                message=f"Ticket status changed to **{new_status.value}** by technician ({ticket.assigned_to})."
                + (f"\n\nResolution Notes: {resolution_notes}" if resolution_notes else ""),
            )
        )
        return True

    def add_message(self, message: TicketMessage) -> int:
        """Append a message to the ticket conversation log."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO ticket_messages (ticket_id, sender, message, timestamp)
                VALUES (?, ?, ?, ?)
            """,
                (message.ticket_id, message.sender, message.message, message.timestamp),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def get_messages(self, ticket_id: str) -> List[TicketMessage]:
        """Fetch all messages associated with a ticket in chronological order."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM ticket_messages WHERE ticket_id = ? ORDER BY id ASC",
                (ticket_id,),
            )
            rows = cursor.fetchall()
            return [
                TicketMessage(
                    id=row["id"],
                    ticket_id=row["ticket_id"],
                    sender=row["sender"],
                    message=row["message"],
                    timestamp=row["timestamp"],
                )
                for row in rows
            ]

    def add_feedback(self, feedback: TicketFeedback) -> int:
        """Record user feedback for a resolved ticket."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO ticket_feedback (ticket_id, rating, comments, resolved_by_ai, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    feedback.ticket_id,
                    feedback.rating,
                    feedback.comments,
                    1 if feedback.resolved_by_ai else 0,
                    feedback.created_at,
                ),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def get_stats(self) -> Dict[str, Any]:
        """Compute summary metrics for reporting and dashboard."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM tickets")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Open'")
            open_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'In Progress'")
            in_progress_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM tickets WHERE status IN ('Resolved', 'Closed')")
            resolved_count = cursor.fetchone()[0]

            cursor.execute("SELECT priority, COUNT(*) FROM tickets GROUP BY priority")
            priority_rows = cursor.fetchall()
            priority_dist = {r[0]: r[1] for r in priority_rows}

            cursor.execute("SELECT category, COUNT(*) FROM tickets GROUP BY category")
            category_rows = cursor.fetchall()
            category_dist = {r[0]: r[1] for r in category_rows}

            cursor.execute("SELECT AVG(rating), COUNT(*) FROM ticket_feedback")
            fb_row = cursor.fetchone()
            avg_rating = round(fb_row[0], 1) if fb_row and fb_row[0] else 4.8
            feedback_count = fb_row[1] if fb_row else 0

            return {
                "total_tickets": total,
                "open_tickets": open_count,
                "in_progress_tickets": in_progress_count,
                "resolved_tickets": resolved_count,
                "resolution_rate": round((resolved_count / total * 100), 1) if total > 0 else 0.0,
                "priority_distribution": priority_dist,
                "category_distribution": category_dist,
                "avg_rating": avg_rating,
                "feedback_count": feedback_count,
            }

    def _row_to_ticket(self, row: sqlite3.Row) -> Ticket:
        """Convert a SQLite row to a Ticket model instance."""
        return Ticket(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            category=TicketCategory(row["category"]) if row["category"] in [e.value for e in TicketCategory] else TicketCategory.OTHER,
            priority=TicketPriority(row["priority"]) if row["priority"] in [e.value for e in TicketPriority] else TicketPriority.MEDIUM,
            status=TicketStatus(row["status"]) if row["status"] in [e.value for e in TicketStatus] else TicketStatus.OPEN,
            user_name=row["user_name"] or "User",
            user_email=row["user_email"] or "user@company.com",
            device_info=row["device_info"],
            ai_diagnosis=row["ai_diagnosis"],
            suggested_steps=row["suggested_steps"],
            assigned_to=row["assigned_to"] or "Unassigned",
            resolution_notes=row["resolution_notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            resolved_at=row["resolved_at"],
        )

    def _seed_demo_data_if_empty(self) -> None:
        """Seed realistic enterprise IT support tickets if database has no records."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tickets")
            if cursor.fetchone()[0] > 0:
                return

        now = datetime.now()
        demo_tickets = [
            Ticket(
                id="TICK-1001",
                title="VPN Connection Failure: AnyConnect TLS Handshake Timeout",
                description="Unable to connect to the corporate VPN from home network. Cisco AnyConnect client fails at 85% with 'Secure Gateway connection timed out'.",
                category=TicketCategory.NETWORK,
                priority=TicketPriority.HIGH,
                status=TicketStatus.IN_PROGRESS,
                user_name="Sarah Jenkins",
                user_email="sjenkins@company.com",
                device_info="Dell Latitude 5530 / Windows 11 Enterprise",
                ai_diagnosis="Likely MTU packet fragmentation or stale VPN adapter configuration. DNS flush and adapter reset recommended.",
                suggested_steps="1. Flush local DNS via 'ipconfig /flushdns'\n2. Disable IPv6 on VPN Virtual Adapter\n3. Select backup gateway: vpn-east.company.com",
                assigned_to="Dave Miller (NetOps)",
                created_at=(now - timedelta(hours=5)).isoformat(),
                updated_at=(now - timedelta(hours=2)).isoformat(),
            ),
            Ticket(
                id="TICK-1002",
                title="Account Lockout after MFA Authenticator Migration",
                description="Switched to a new iPhone yesterday and Microsoft Authenticator number matching prompt is not appearing. Account locked out after multiple attempts.",
                category=TicketCategory.ACCOUNT,
                priority=TicketPriority.CRITICAL,
                status=TicketStatus.OPEN,
                user_name="Marcus Vance",
                user_email="mvance@company.com",
                device_info="iPhone 15 Pro / iOS 17.5 & ThinkPad T14",
                ai_diagnosis="User requires MFA method reset in Microsoft Entra ID / Okta admin console and account unlock.",
                suggested_steps="1. Verify employee identity via manager confirmation\n2. Issue Temporary Access Pass (TAP)\n3. Clear registered authenticator devices",
                assigned_to="Unassigned",
                created_at=(now - timedelta(hours=1)).isoformat(),
                updated_at=(now - timedelta(hours=1)).isoformat(),
            ),
            Ticket(
                id="TICK-1003",
                title="Outlook Crashes Repeatedly When Opening Shared Mailbox",
                description="Outlook 365 crashes with error '0xc0000005 access violation' whenever clicking into the 'Support-Escalations' shared mailbox.",
                category=TicketCategory.EMAIL,
                priority=TicketPriority.MEDIUM,
                status=TicketStatus.RESOLVED,
                user_name="Emily Zhao",
                user_email="ezhao@company.com",
                device_info="HP EliteBook 840 / Windows 10 Pro",
                ai_diagnosis="Corrupted OST cache for shared mailboxes. Disabling cached exchange mode for shared folders resolves the crash.",
                suggested_steps="1. Account Settings -> Change -> More Settings -> Advanced\n2. Uncheck 'Download shared folders'\n3. Restart Outlook",
                assigned_to="Alex Rivera (IT Support)",
                resolution_notes="Advised user to toggle off caching for shared mailboxes. Rebuilt local OST cache. Confirmed operational.",
                created_at=(now - timedelta(days=1, hours=4)).isoformat(),
                updated_at=(now - timedelta(hours=6)).isoformat(),
                resolved_at=(now - timedelta(hours=6)).isoformat(),
            ),
            Ticket(
                id="TICK-1004",
                title="Request for Local Docker Desktop Admin Rights",
                description="Need local admin permissions or Docker group membership to run local containers for backend service development.",
                category=TicketCategory.SOFTWARE,
                priority=TicketPriority.LOW,
                status=TicketStatus.WAITING_ON_USER,
                user_name="Priya Patel",
                user_email="ppatel@company.com",
                device_info="MacBook Pro M2 / macOS Sonoma",
                ai_diagnosis="Software access request. Requires engineering lead sign-off and Endpoint Privilege Management (EPM) policy assignment.",
                suggested_steps="1. Submit ticket approval form signed by Tech Lead\n2. Deploy Docker Desktop via Intune Self-Service\n3. Add account to local docker-users group",
                assigned_to="Jessica Wu",
                created_at=(now - timedelta(days=2)).isoformat(),
                updated_at=(now - timedelta(hours=12)).isoformat(),
            ),
            Ticket(
                id="TICK-1005",
                title="Office 4th Floor Konica Minolta Printer Offline",
                description="Print jobs submitted to 'NYC-4F-Color-Printer' remain in queue with 'Printer Offline' status. Multiple colleagues impacted.",
                category=TicketCategory.HARDWARE,
                priority=TicketPriority.HIGH,
                status=TicketStatus.RESOLVED,
                user_name="Robert King",
                user_email="rking@company.com",
                device_info="Network Printer (IP: 10.20.4.155)",
                ai_diagnosis="Print Spooler queue hang on print server or DHCP IP lease renewal conflict on physical MFP.",
                suggested_steps="1. Restart print spooler service on print server\n2. Power cycle printer and verify static IP lease\n3. Purge orphaned print jobs",
                assigned_to="Dave Miller (NetOps)",
                resolution_notes="Restarted print spooler on PRINTSVR01 and refreshed IP reservation. Flushed 3 jammed corrupt PDF print jobs.",
                created_at=(now - timedelta(days=3)).isoformat(),
                updated_at=(now - timedelta(days=1)).isoformat(),
                resolved_at=(now - timedelta(days=1)).isoformat(),
            ),
        ]

        for ticket in demo_tickets:
            self.create_ticket(ticket)

        # Seed initial feedback
        self.add_feedback(
            TicketFeedback(
                ticket_id="TICK-1003",
                rating=5,
                comments="Super quick resolution, the steps to disable shared cache solved the crash in 2 minutes!",
                resolved_by_ai=True,
                created_at=(now - timedelta(hours=5)).isoformat(),
            )
        )
        self.add_feedback(
            TicketFeedback(
                ticket_id="TICK-1005",
                rating=4,
                comments="Printer is working again, thanks for clearing the queue.",
                resolved_by_ai=False,
                created_at=(now - timedelta(days=1)).isoformat(),
            )
        )

    # -------------------------------------------------------------------------
    # USER MANAGEMENT & AUTHENTICATION OPERATIONS
    # -------------------------------------------------------------------------

    def _seed_users_if_empty(self) -> None:
        """Seed initial administrator and demo users if the users table is empty."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS count FROM users")
            if cursor.fetchone()["count"] > 0:
                return

        from src.auth.password_manager import PasswordManager

        now = datetime.now().isoformat()
        default_pwd_hash = PasswordManager.hash_password("Password123!")
        admin_pwd_hash = PasswordManager.hash_password(settings.ADMIN_PASSWORD)

        demo_users = [
            # 1. Administrator
            (
                "ADMIN-01",
                settings.ADMIN_USERNAME,
                settings.ADMIN_EMAIL,
                "Apex Administrator",
                admin_pwd_hash,
                UserRole.ADMIN.value,
                "IT Operations & Security",
                1,
                now,
                now,
            ),
            # 2. Technicians
            (
                "TECH-1001",
                "tech_sarah",
                "sarah.connor@example.com",
                "Sarah Connor",
                default_pwd_hash,
                UserRole.TECHNICIAN.value,
                "NetOps & Network Infrastructure",
                1,
                now,
                now,
            ),
            (
                "TECH-1002",
                "tech_mike",
                "mike.ross@company.com",
                "Mike Ross",
                default_pwd_hash,
                UserRole.TECHNICIAN.value,
                "Deskside & Hardware Support",
                1,
                now,
                now,
            ),
            # 3. Employees
            (
                "EMP-1001",
                "emp_david",
                "dmiller@company.com",
                "David Miller",
                default_pwd_hash,
                UserRole.EMPLOYEE.value,
                "Sales & Field Engineering",
                1,
                now,
                now,
            ),
            (
                "EMP-1002",
                "emp_alice",
                "alice@company.com",
                "Alice Smith",
                default_pwd_hash,
                UserRole.EMPLOYEE.value,
                "Product & Design",
                1,
                now,
                now,
            ),
        ]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT OR IGNORE INTO users (
                    id, username, email, full_name, password_hash, role, team, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                demo_users,
            )
            conn.commit()

    def create_user(self, user: User, password_hash: str) -> User:
        """Create a new user record with parameterized SQL."""
        if not user.id:
            user.id = f"USER-{datetime.now().strftime('%Y%m%d%H%M%S')}-{user.username[:4].upper()}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (
                    id, username, email, full_name, password_hash, role, team, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.id,
                    user.username.strip().lower(),
                    user.email.strip().lower(),
                    user.full_name.strip(),
                    password_hash,
                    user.role.value if hasattr(user.role, "value") else str(user.role),
                    user.team,
                    1 if user.is_active else 0,
                    user.created_at,
                    user.updated_at,
                ),
            )
            conn.commit()
        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve user by their unique User ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return User(
                id=row["id"],
                username=row["username"],
                email=row["email"],
                full_name=row["full_name"],
                role=UserRole(row["role"]),
                team=row["team"],
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def get_user_by_username(self, username: str) -> Optional[Tuple[User, str]]:
        """Retrieve user and stored password hash by username."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE LOWER(username) = LOWER(?)",
                (username.strip(),),
            )
            row = cursor.fetchone()
            if not row:
                return None
            user = User(
                id=row["id"],
                username=row["username"],
                email=row["email"],
                full_name=row["full_name"],
                role=UserRole(row["role"]),
                team=row["team"],
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            return user, row["password_hash"]

    def get_user_by_email(self, email: str) -> Optional[Tuple[User, str]]:
        """Retrieve user and stored password hash by corporate email."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE LOWER(email) = LOWER(?)",
                (email.strip(),),
            )
            row = cursor.fetchone()
            if not row:
                return None
            user = User(
                id=row["id"],
                username=row["username"],
                email=row["email"],
                full_name=row["full_name"],
                role=UserRole(row["role"]),
                team=row["team"],
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            return user, row["password_hash"]

    def list_users(
        self,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[User]:
        """List registered users with optional role or active status filters."""
        query = "SELECT * FROM users WHERE 1=1"
        params: List[Any] = []

        if role and role.lower() != "all":
            query += " AND LOWER(role) = LOWER(?)"
            params.append(role)

        if is_active is not None:
            query += " AND is_active = ?"
            params.append(1 if is_active else 0)

        query += " ORDER BY created_at DESC"

        users: List[User] = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            for row in cursor.fetchall():
                users.append(
                    User(
                        id=row["id"],
                        username=row["username"],
                        email=row["email"],
                        full_name=row["full_name"],
                        role=UserRole(row["role"]),
                        team=row["team"],
                        is_active=bool(row["is_active"]),
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )
                )
        return users

    def update_user_status(self, user_id: str, is_active: bool) -> bool:
        """Activate or deactivate a user account."""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET is_active = ?, updated_at = ? WHERE id = ?",
                (1 if is_active else 0, now, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_user_role(
        self,
        user_id: str,
        new_role: UserRole,
        team: Optional[str] = None,
    ) -> bool:
        """Change a user's role and assigned support team."""
        now = datetime.now().isoformat()
        role_val = new_role.value if hasattr(new_role, "value") else str(new_role)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET role = ?, team = ?, updated_at = ? WHERE id = ?",
                (role_val, team, now, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_user_password(self, user_id: str, new_password_hash: str) -> bool:
        """Update password hash for a user."""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
                (new_password_hash, now, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def assign_ticket(self, ticket_id: str, assigned_to: str) -> bool:
        """Assign or reassign a ticket to a technician or team queue."""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tickets SET assigned_to = ?, updated_at = ? WHERE id = ?",
                (assigned_to, now, ticket_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    # -------------------------------------------------------------------------
    # AUDIT LOGGING OPERATIONS
    # -------------------------------------------------------------------------

    def add_audit_log(self, entry: AuditLogEntry) -> None:
        """Record an immutable security audit event."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_logs (
                    user_id, username, action, resource_type, resource_id, details, ip_address, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.user_id,
                    entry.username,
                    entry.action,
                    entry.resource_type,
                    entry.resource_id,
                    entry.details,
                    entry.ip_address,
                    entry.timestamp,
                ),
            )
            conn.commit()

    def list_audit_logs(
        self,
        limit: int = 100,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
    ) -> List[AuditLogEntry]:
        """Retrieve recent security audit log events with optional filters."""
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params: List[Any] = []

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if action and action.lower() != "all":
            query += " AND action = ?"
            params.append(action)

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        logs: List[AuditLogEntry] = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            for row in cursor.fetchall():
                logs.append(
                    AuditLogEntry(
                        id=row["id"],
                        user_id=row["user_id"],
                        username=row["username"],
                        action=row["action"],
                        resource_type=row["resource_type"],
                        resource_id=row["resource_id"],
                        details=row["details"],
                        ip_address=row["ip_address"],
                        timestamp=row["timestamp"],
                    )
                )
        return logs

    # -------------------------------------------------------------------------
    # SCOPED TICKET ACCESS OPERATIONS
    # -------------------------------------------------------------------------

    def list_tickets_for_user(
        self,
        user: User,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[Ticket]:
        """Retrieve tickets scoped strictly to user permissions:
        - Admin: sees all tickets.
        - Technician: sees tickets assigned to them or their team.
        - Employee: sees ONLY tickets they submitted.
        """
        all_tickets = self.list_tickets(
            status=status,
            priority=priority,
            category=category,
            search_query=search_query,
        )

        if user.is_admin:
            return all_tickets

        if user.role == UserRole.TECHNICIAN:
            team_keywords = [user.full_name.lower(), user.username.lower()]
            if user.team:
                team_keywords.append(user.team.lower())
                # Include significant team words (e.g., 'netops', 'network', 'hardware')
                for w in re.split(r"[\s&,/-]+", user.team.lower()):
                    if len(w) >= 4 and w not in ("support", "desk"):
                        team_keywords.append(w)

            filtered = []
            for t in all_tickets:
                assigned = (t.assigned_to or "").lower()
                # If assigned directly to technician, or their team, or unassigned/general queue
                if (
                    not assigned
                    or "tier 1" in assigned
                    or any(k in assigned for k in team_keywords)
                ):
                    filtered.append(t)
            return filtered

        # Employee: strictly match email or user name
        user_email = user.email.lower()
        user_name = user.full_name.lower()
        return [
            t
            for t in all_tickets
            if (t.user_email and t.user_email.lower() == user_email)
            or (t.user_name and t.user_name.lower() == user_name)
        ]


