"""
Model cơ sở dữ liệu cho Tài liệu khoa học (Paper) và Kết quả phân tích bài báo (PaperAnalysis).
Quản lý thông tin metadata của bài báo (tác giả, abstract, nguồn, PDF) và nội dung trích xuất có cấu trúc.
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Paper(Base):
    """
    Bảng papers: Lưu trữ thông tin metadata của các bài báo khoa học được thu thập hoặc tải lên.
    """
    __tablename__ = "papers"

    # Khóa chính dạng UUID
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Khóa ngoại liên kết với phiên nghiên cứu
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False)
    
    # Tiêu đề bài báo
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    # Danh sách tên tác giả
    authors: Mapped[List[str]] = mapped_column(JSON, default=list)
    # Tóm tắt gốc (Abstract)
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Năm xuất bản
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Tạp chí / Hội nghị phát hành (Venue)
    venue: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Mã định danh số (DOI)
    doi: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Đường dẫn liên kết trực tuyến
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # Đường dẫn file PDF lưu trên ổ cứng cục bộ (nếu có)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # Nguồn bài báo: arxiv, semantic_scholar, upload
    source: Mapped[str] = mapped_column(String(50), default="arxiv")
    # Điểm số độ liên quan với câu hỏi nghiên cứu (0.0 -> 1.0)
    relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    # Đánh dấu bài báo có được chọn để đưa vào tổng quan hay không
    is_selected: Mapped[bool] = mapped_column(Boolean, default=True)
    # Trạng thái xử lý nội dung: PENDING, PROCESSED, FAILED
    ingestion_status: Mapped[str] = mapped_column(String(50), default="PENDING")
    
    # Thời điểm tạo bản ghi
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Các mối quan hệ (Relationships)
    session = relationship("ResearchSession", back_populates="papers")
    analysis = relationship("PaperAnalysis", back_populates="paper", uselist=False, cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="paper", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="paper", cascade="all, delete-orphan")


class PaperAnalysis(Base):
    """
    Bảng paper_analyses: Lưu kết quả phân tích có cấu trúc từ ReadingAgent cho từng bài báo.
    Bao gồm phương pháp, bộ dữ liệu, chỉ số đánh giá, kết quả và hạn chế.
    """
    __tablename__ = "paper_analyses"

    # Khóa chính dạng UUID
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Khóa ngoại liên kết 1-1 với bài báo
    paper_id: Mapped[str] = mapped_column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Phương pháp chính (Methodology)
    method: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Bộ dữ liệu thực nghiệm (Dataset)
    dataset: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Các chỉ số đánh giá (Evaluation Metrics)
    metrics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Kết quả và đóng góp chính (Key Results)
    results: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Hạn chế / Hướng phát triển (Limitations & Future Work)
    limitations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Tóm tắt toàn diện bài báo
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Dữ liệu JSON phân tích thô từ LLM
    raw_analysis: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Thời điểm phân tích
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Quan hệ ngược về bài báo
    paper = relationship("Paper", back_populates="analysis")

