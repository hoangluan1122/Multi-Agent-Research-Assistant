"""
Package chứa toàn bộ Pydantic Schemas (Data Transfer Objects - DTOs) của hệ thống PaperFlow.
Dùng để xác thực (validation), tuần tự hóa (serialization) dữ liệu đầu vào/đầu ra của các API.
"""

from app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionDetailResponse,
)
from app.schemas.paper import (
    PaperSearchRequest,
    PaperCreate,
    PaperResponse,
    PaperAnalysisResponse,
    PaperSelectionUpdate,
)
from app.schemas.report import (
    ReportResponse,
    ReviewResponse,
    CitationResponse,
    ExportRequest,
)
from app.schemas.agent import (
    AgentRunResponse,
    WorkflowStartRequest,
    WorkflowStatusResponse,
)
from app.schemas.config import (
    SystemConfigResponse,
    SystemConfigUpdate,
)

__all__ = [
    "SessionCreate",
    "SessionUpdate",
    "SessionResponse",
    "SessionDetailResponse",
    "PaperSearchRequest",
    "PaperCreate",
    "PaperResponse",
    "PaperAnalysisResponse",
    "PaperSelectionUpdate",
    "ReportResponse",
    "ReviewResponse",
    "CitationResponse",
    "ExportRequest",
    "AgentRunResponse",
    "WorkflowStartRequest",
    "WorkflowStatusResponse",
    "SystemConfigResponse",
    "SystemConfigUpdate",
]

