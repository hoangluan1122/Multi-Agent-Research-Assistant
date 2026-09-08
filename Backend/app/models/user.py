"""
Model cơ sở dữ liệu cho Tài khoản người dùng (User).
Quản lý thông tin tài khoản, mật khẩu băm, và quan hệ sở hữu các phiên nghiên cứu.
"""

import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class User(Base):
    """
    Bảng users: Lưu trữ thông tin tài khoản người dùng của hệ thống PaperFlow.
    """
    __tablename__ = "users"

    # Khóa chính dạng UUID
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Địa chỉ Email (Duy nhất)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    
    # Mật khẩu đã băm an toàn
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Họ và tên người dùng
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Researcher")
    
    # Đường dẫn ảnh đại diện (Tùy chọn)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Trạng thái kích hoạt tài khoản
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Vai trò: user, admin
    role: Mapped[str] = mapped_column(String(50), default="user")
    
    # Thời điểm tạo tài khoản
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Quan hệ 1-Nhiều: Một User sở hữu nhiều ResearchSession
    sessions = relationship("ResearchSession", back_populates="user", cascade="all, delete-orphan", lazy="selectin")

