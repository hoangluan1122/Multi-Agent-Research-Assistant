"""
Pydantic Schemas liên quan đến Báo cáo (Report), Đánh giá (Review), Trích dẫn (Citation) và Xuất file (Export).
Định nghĩa cấu trúc dữ liệu cho báo cáo tổng quan, phản biện chất lượng và cấu hình xuất tài liệu (.md, .docx, .pdf).
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class ReviewResponse(BaseModel):
    """Schema dữ liệu trả về thông tin kết quả đánh giá, chấm điểm và thẩm định rủi ro ảo giác."""
    id: str
    report_id: str
    session_id: str
    score: float
    status: str
    issues: List[Dict[str, Any]] = []
    feedback: Optional[str] = None
    hallucination_risks: List[Dict[str, Any]] = []
    citation_coverage: float
    created_at: datetime

    class Config:
        from_attributes = True

class ReportResponse(BaseModel):
    """Schema dữ liệu trả về thông tin báo cáo nghiên cứu hoàn chỉnh cùng lịch sử các lần đánh giá."""
    id: str
    session_id: str
    title: str
    outline: List[Dict[str, Any]] = []
    content: str
    comparison_table: Optional[str] = None
    version: int
    review_status: str
    created_at: datetime
    updated_at: datetime
    reviews: List[ReviewResponse] = []

    class Config:
        from_attributes = True

class CitationResponse(BaseModel):
    """Schema dữ liệu trả về thông tin trích dẫn tham khảo chuẩn học thuật."""
    id: str
    session_id: str
    paper_id: str
    claim_text: Optional[str] = None
    citation_key: Optional[str] = None
    citation_text: str
    style: str
    is_verified: bool
    verification_status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ExportRequest(BaseModel):
    """Schema yêu cầu xuất báo cáo sang các định dạng khác nhau (Markdown, Word docx, PDF)."""
    format: str = Field("markdown", pattern="^(markdown|docx|pdf)$", description="Định dạng xuất báo cáo")
    include_citations: bool = Field(True, description="Đính kèm danh mục tài liệu tham khảo")
    include_comparison_table: bool = Field(True, description="Đính kèm bảng so sánh tổng hợp")

