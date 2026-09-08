"""
Pydantic Schemas liên quan đến Xác thực và Tài khoản người dùng (User & Auth).
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    """Schema dữ liệu khi Đăng ký tài khoản mới."""
    email: str = Field(..., min_length=3, max_length=255, description="Địa chỉ email đăng nhập")
    password: str = Field(..., min_length=6, description="Mật khẩu tối thiểu 6 ký tự")
    full_name: str = Field(..., min_length=2, description="Họ và tên người dùng")

class UserLogin(BaseModel):
    """Schema dữ liệu khi Đăng nhập."""
    email: str = Field(..., description="Địa chỉ email")
    password: str = Field(..., description="Mật khẩu")

class UserResponse(BaseModel):
    """Schema dữ liệu trả về thông tin tài khoản."""
    id: str
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """Schema dữ liệu trả về khi đăng nhập thành công."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

