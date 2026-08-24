"""
Model cơ sở dữ liệu cho Báo cáo tổng quan nghiên cứu (Report) và Đánh giá thẩm định (Review).
Lưu trữ nội dung Markdown của báo cáo, bảng so sánh tổng hợp, phiên bản và kết quả chấm điểm chất lượng (score, hallucination check).
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Report(Base):
    """
    Bảng reports: Lưu trữ bản báo cáo tổng quan tài liệu (Literature Review) được tạo tự động bởi WritingAgent.
    """
    __tablename__ = "reports"

    # Khóa chính dạng UUID
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Khóa ngoại liên kết với phiên nghiên cứu
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False)
    
    # Tiêu đề báo cáo
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    # Cấu trúc dàn ý chi tiết của báo cáo
    outline: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    # Toàn bộ nội dung báo cáo dạng Markdown
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Bảng tổng hợp so sánh phương pháp/kết quả (định dạng Markdown table hoặc JSON)
    comparison_table: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Số thứ tự phiên bản báo cáo (tăng lên nếu phải viết lại sau khi Review không đạt)
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    # Trạng thái thẩm định: DRAFT, REVIEWING, PASS, FAIL
    review_status: Mapped[str] = mapped_column(String(50), default="DRAFT")
    
    # Thời điểm tạo và cập nhật gần nhất
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Các mối quan hệ liên kết (Relationships)
    session = relationship("ResearchSession", back_populates="reports")
    reviews = relationship("Review", back_populates="report", cascade="all, delete-orphan")


class Review(Base):
    """
    Bảng reviews: Lưu kết quả phản biện, kiểm tra ảo giác và chấm điểm của ReviewAgent đối với báo cáo.
    """
    __tablename__ = "reviews"

    # Khóa chính dạng UUID
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Khóa ngoại liên kết với báo cáo cần thẩm định
    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    # ID phiên nghiên cứu
    session_id: Mapped[str] = mapped_column(String(36), nullable=False)
    
    # Điểm đánh giá chất lượng (thang điểm 0 - 100)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    # Kết luận thẩm định: PASS (Đạt) hoặc FAIL (Chưa đạt)
    status: Mapped[str] = mapped_column(String(20), default="PASS")
    # Danh sách các vấn đề được phát hiện
    issues: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    # Nhận xét góp ý chi tiết của ReviewAgent
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Rủi ro ảo giác thông tin và trích dẫn sai lệch
    hallucination_risks: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    # Tỷ lệ bao phủ trích dẫn hợp lệ (0.0 -> 1.0)
    citation_coverage: Mapped[float] = mapped_column(Float, default=1.0)
    
    # Thời điểm thẩm định
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Quan hệ ngược về báo cáo
    report = relationship("Report", back_populates="reviews")

