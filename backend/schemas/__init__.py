"""Pydantic schemas module."""
from backend.schemas.auth import LoginRequest, LoginResponse, UserResponse
from backend.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatFeedbackRequest,
    ChatEscalateRequest,
    SourceCitation,
)
from backend.schemas.ticket import (
    TicketCreateRequest,
    TicketUpdateRequest,
    TicketNoteRequest,
    TicketResponse,
    TicketMessageResponse,
    TriagePreviewRequest,
    TriagePreviewResponse,
)
from backend.schemas.user import (
    UserCreateRequest,
    UserStatusUpdateRequest,
    UserRoleUpdateRequest,
    AuditLogResponse,
)
from backend.schemas.dashboard import DashboardStatsResponse
from backend.schemas.knowledge import (
    DocumentItem,
    SearchResultChunk,
    KnowledgeSearchRequest,
    ReindexResponse,
)

