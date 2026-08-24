"""
Package điều phối quy trình (Orchestrator) của hệ thống PaperFlow:
- WorkflowState: Lớp trạng thái vòng đời của workflow.
- WorkflowEventBroadcaster (workflow_broadcaster): Quản lý phát sự kiện SSE thời gian thực.
- ResearchWorkflowEngine (workflow_engine): Động cơ điều phối toàn bộ chu trình Multi-Agent từ tìm kiếm đến thẩm định.
"""

from app.orchestrator.state import WorkflowState, workflow_broadcaster
from app.orchestrator.workflow import workflow_engine, ResearchWorkflowEngine

__all__ = [
    "WorkflowState",
    "workflow_broadcaster",
    "workflow_engine",
    "ResearchWorkflowEngine",
]

