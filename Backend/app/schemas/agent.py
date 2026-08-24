"""
Pydantic Schemas liên quan đến Agent và Multi-Agent Workflow.
Định nghĩa cấu trúc dữ liệu cho lịch sử chạy agent, yêu cầu bắt đầu workflow và trạng thái tiến trình thời gian thực.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

class AgentRunResponse(BaseModel):
    """Schema dữ liệu trả về thông tin chi tiết của một lần thực thi Agent."""
    id: str
    session_id: str
    agent_name: str
    status: str
    step_description: Optional[str] = None
    input_data: Dict[str, Any] = {}
    output_data: Dict[str, Any] = {}
    error_message: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class WorkflowStartRequest(BaseModel):
    """Schema yêu cầu khởi động quy trình Multi-Agent tự động cho một phiên nghiên cứu."""
    session_id: str
    auto_search: bool = True               # Tự động tìm kiếm bài báo nếu chưa có
    auto_select_papers: bool = True        # Tự động chọn các bài báo có độ liên quan cao nhất
    max_papers: int = 5                    # Số lượng bài báo tối đa đưa vào tổng hợp
    custom_outline: Optional[List[str]] = None  # Dàn ý tùy chỉnh do người dùng cung cấp (nếu có)

class WorkflowStatusResponse(BaseModel):
    """Schema dữ liệu phản hồi trạng thái hiện tại của quy trình Multi-Agent."""
    session_id: str
    status: str                            # Trạng thái tổng thể: RUNNING, COMPLETED, FAILED
    current_step: str                      # Bước hiện tại (ví dụ: READING, WRITING)
    current_agent: Optional[str] = None    # Agent đang hoạt động
    progress_percentage: int = 0           # Phần trăm hoàn thành (0 - 100%)
    message: str = ""                      # Thông điệp trạng thái thân thiện cho UI
    agent_runs: List[AgentRunResponse] = [] # Danh sách lịch sử chạy của các agent
    error_message: Optional[str] = None    # Lỗi nếu có

