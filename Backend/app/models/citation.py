"""
Model cơ sở dữ liệu cho Trích dẫn học thuật (Citation).
Quản lý các trích dẫn trong báo cáo nghiên cứu, định dạng trích dẫn (IEEE, APA) và trạng thái kiểm chứng độ chính xác (Anti-hallucination verification).
"""

import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Citation(Base):
    """
    Bảng citations: Lưu thông tin trích dẫn tham khảo chuẩn học thuật được liên kết giữa bài báo và báo cáo.
    """
    __tablename__ = "citations"

    # Khóa chính dạng UUID
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Khóa ngoại liên kết với phiên nghiên cứu
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False)
    # Khóa ngoại liên kết với bài báo được trích dẫn
    paper_id: Mapped[str] = mapped_column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    
    # Luận điểm hoặc câu văn được bảo chứng bởi trích dẫn này
    claim_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Ký hiệu trích dẫn (ví dụ: [1] hoặc [Vaswani et al., 2017])
    citation_key: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Chuỗi trích dẫn đầy đủ theo chuẩn tham khảo
    citation_text: Mapped[str] = mapped_column(Text, nullable=False)
    # Phong cách trích dẫn: IEEE, APA
    style: Mapped[str] = mapped_column(String(20), default="IEEE")
    # Cờ đánh dấu đã được kiểm chứng với nội dung bài báo gốc hay chưa
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    # Trạng thái thẩm định trích dẫn: VERIFIED, UNVERIFIED, MISSING
    verification_status: Mapped[str] = mapped_column(String(50), default="VERIFIED")
    
    # Thời điểm tạo trích dẫn
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Các mối quan hệ liên kết (Relationships)
    session = relationship("ResearchSession", back_populates="citations")
    paper = relationship("Paper", back_populates="citations")

