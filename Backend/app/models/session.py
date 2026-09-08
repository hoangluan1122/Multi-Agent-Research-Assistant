"""
Model cơ sở dữ liệu cho Phiên nghiên cứu khoa học (ResearchSession).
Quản lý thông tin chủ đề nghiên cứu, câu hỏi nghiên cứu, trạng thái vòng đời phiên và liên kết với các thực thể khác.
"""

import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class ResearchSession(Base):
    """
    Bảng research_sessions: Đại diện cho một phiên làm việc / dự án nghiên cứu tổng quan.
    Bao gồm thông tin đề tài, trạng thái tiến trình (READY, SEARCHING, READING, SUMMARIZING, CITING, WRITING, REVIEWING, COMPLETED, FAILED).
    """
    __tablename__ = "research_sessions"

    # Khóa chính dạng UUID
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Khóa ngoại liên kết với User (Nullable để tương thích với chế độ Khách / Guest)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Chủ đề nghiên cứu chính (Topic)
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    # Câu hỏi nghiên cứu chi tiết (Research Question)
    research_question: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Tham số tùy chỉnh của phiên (nhà cung cấp LLM, độ dài, kiểu trích dẫn...)
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Trạng thái tổng thể: READY, RUNNING, REVIEWING, COMPLETED, FAILED
    status: Mapped[str] = mapped_column(String(50), default="READY")
    # Bước thực hiện hiện tại của Multi-Agent workflow
    current_step: Mapped[str] = mapped_column(String(100), default="INITIALIZED")
    # Thông báo lỗi chi tiết nếu phiên gặp sự cố
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Thời điểm tạo và cập nhật gần nhất
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Các mối quan hệ (Relationships) liên kết với các bảng con
    user = relationship("User", back_populates="sessions")
    papers = relationship("Paper", back_populates="session", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="session", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="session", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="session", cascade="all, delete-orphan")

