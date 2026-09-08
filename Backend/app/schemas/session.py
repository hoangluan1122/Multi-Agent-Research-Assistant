"""
Pydantic Schemas liên quan đến Phiên nghiên cứu (ResearchSession).
Định nghĩa cấu trúc dữ liệu cho tạo mới phiên, cập nhật thông tin và trả về danh sách/chi tiết phiên nghiên cứu.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

class SessionCreate(BaseModel):
    """Schema dữ liệu đầu vào khi người dùng tạo mới một phiên nghiên cứu."""
    topic: str = Field(..., min_length=3, max_length=500, description="Chủ đề nghiên cứu khoa học")
    research_question: Optional[str] = Field(None, description="Câu hỏi nghiên cứu chi tiết cần giải quyết")
    year_start: Optional[int] = Field(None, ge=1990, le=2030, description="Năm bắt đầu lọc paper")
    year_end: Optional[int] = Field(None, ge=1990, le=2030, description="Năm kết thúc lọc paper")
    max_papers: Optional[int] = Field(10, ge=1, le=50, description="Số lượng bài báo tối đa")
    sources: Optional[List[str]] = Field(default=["arxiv", "semantic_scholar"], description="Nguồn dữ liệu học thuật")
    citation_style: Optional[str] = Field("IEEE", description="Định dạng trích dẫn (IEEE / APA)")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Các tham số bổ sung khác")

class SessionUpdate(BaseModel):
    """Schema dữ liệu cho phép cập nhật chủ đề hoặc câu hỏi nghiên cứu của phiên."""
    topic: Optional[str] = None
    research_question: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

class SessionResponse(BaseModel):
    """Schema dữ liệu trả về thông tin tóm tắt của một phiên nghiên cứu."""
    id: str
    user_id: Optional[str] = None
    topic: str
    research_question: Optional[str] = None
    parameters: Dict[str, Any] = {}
    status: str
    current_step: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SessionDetailResponse(SessionResponse):
    """Schema dữ liệu trả về thông tin chi tiết của phiên (bao gồm số lượng bài báo và trạng thái báo cáo)."""
    paper_count: int = 0
    has_report: bool = False
    latest_report_id: Optional[str] = None

