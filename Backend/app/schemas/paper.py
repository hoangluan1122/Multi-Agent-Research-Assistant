"""
Pydantic Schemas liên quan đến Tài liệu khoa học (Paper) và Phân tích bài báo (PaperAnalysis).
Định nghĩa cấu trúc dữ liệu cho tìm kiếm bài báo, tạo mới, phân tích trích xuất thông tin và cập nhật lựa chọn.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class PaperSearchRequest(BaseModel):
    """Schema yêu cầu tìm kiếm bài báo học thuật qua Semantic Scholar / arXiv."""
    session_id: str
    query: str = Field(..., min_length=2, description="Từ khóa hoặc câu truy vấn tìm kiếm")
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    max_results: Optional[int] = Field(10, ge=1, le=50, description="Số lượng kết quả tối đa")
    sources: Optional[List[str]] = Field(default=["arxiv", "semantic_scholar"], description="Nguồn tìm kiếm")

class PaperCreate(BaseModel):
    """Schema dữ liệu tạo mới bài báo khi tải file PDF lên thủ công."""
    session_id: str
    title: str
    authors: List[str] = []
    abstract: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    pdf_path: Optional[str] = None
    source: str = "upload"
    relevance_score: float = 1.0

class PaperAnalysisResponse(BaseModel):
    """Schema dữ liệu trả về kết quả phân tích có cấu trúc của bài báo."""
    id: str
    paper_id: str
    method: Optional[str] = None
    dataset: Optional[str] = None
    metrics: Optional[str] = None
    results: Optional[str] = None
    limitations: Optional[str] = None
    summary: Optional[str] = None
    raw_analysis: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True

class PaperResponse(BaseModel):
    """Schema dữ liệu trả về thông tin đầy đủ của bài báo bao gồm cả phân tích."""
    id: str
    session_id: str
    title: str
    authors: List[str] = []
    abstract: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    source: str
    relevance_score: float
    is_selected: bool
    ingestion_status: str
    created_at: datetime
    analysis: Optional[PaperAnalysisResponse] = None

    class Config:
        from_attributes = True

class PaperSelectionUpdate(BaseModel):
    """Schema yêu cầu chọn hoặc bỏ chọn danh sách bài báo tham gia tổng hợp."""
    paper_ids: List[str]
    is_selected: bool = True

