"""
Model cơ sở dữ liệu cho Lịch sử thực thi của Agent (AgentRun).
Ghi nhận nhật ký chạy từng bước của các Agent (SearchAgent, ReadingAgent, SummarizationAgent, CitationAgent, WritingAgent, ReviewAgent), bao gồm input, output, lỗi và thời gian.
"""

import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class AgentRun(Base):
    """
    Bảng agent_runs: Lưu nhật ký (Audit trail) từng phiên chạy của từng agent trong workflow.
    """
    __tablename__ = "agent_runs"

    # Khóa chính dạng UUID
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Khóa ngoại liên kết với phiên nghiên cứu
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False)
    
    # Tên Agent: SearchAgent, ReadingAgent, SummarizationAgent, CitationAgent, WritingAgent, ReviewAgent
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Trạng thái thực thi: RUNNING, COMPLETED, FAILED
    status: Mapped[str] = mapped_column(String(50), default="RUNNING")
    # Mô tả ngắn gọn về hành động/bước đang thực hiện
    step_description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Dữ liệu đầu vào của Agent dạng JSON
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    # Dữ liệu đầu ra của Agent dạng JSON
    output_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    # Chi tiết lỗi nếu agent thực thi thất bại
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Thời điểm bắt đầu và kết thúc
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Quan hệ liên kết với phiên nghiên cứu
    session = relationship("ResearchSession", back_populates="agent_runs")

