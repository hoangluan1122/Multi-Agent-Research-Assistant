"""
Model cơ sở dữ liệu cho các phân đoạn văn bản của tài liệu (DocumentChunk).
Lưu trữ nội dung text đã chia nhỏ (chunking), chỉ số trang/phần và liên kết vector embedding trong Qdrant.
"""

import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class DocumentChunk(Base):
    """
    Bảng document_chunks: Lưu từng đoạn văn bản được băm nhỏ từ tài liệu PDF phục vụ tìm kiếm ngữ nghĩa RAG.
    """
    __tablename__ = "document_chunks"

    # Khóa chính dạng UUID
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Khóa ngoại liên kết với bài báo gốc
    paper_id: Mapped[str] = mapped_column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    # ID của phiên nghiên cứu
    session_id: Mapped[str] = mapped_column(String(36), nullable=False)
    
    # Thứ tự đoạn văn bản trong tài liệu
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    # Số trang trong tài liệu gốc (nếu trích xuất được)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Tên phân mục (Section: Abstract, Introduction, Method, etc.)
    section_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Nội dung văn bản của đoạn
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # Định danh điểm dữ liệu vector tương ứng trong cơ sở dữ liệu Qdrant
    embedding_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Thời điểm tạo chunk
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Quan hệ liên kết với bài báo
    paper = relationship("Paper", back_populates="chunks")

