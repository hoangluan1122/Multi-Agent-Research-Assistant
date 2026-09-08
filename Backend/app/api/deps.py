"""
Dependency Injection phụ trách xác thực người dùng qua JWT Token.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.core.security import decode_access_token

# Khởi tạo HTTPBearer header extractor (không bắt buộc redirect form)
http_bearer = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency bắt buộc người dùng phải đăng nhập và gửi kèm token hợp lệ.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yêu cầu xác thực tài khoản. Vui lòng đăng nhập.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập không hợp lệ hoặc đã hết hạn.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload["sub"]
    stmt = select(User).where(User.id == user_id, User.is_active.is_(True))
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản không tồn tại hoặc đã bị vô hiệu hóa.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Dependency tùy chọn: Trả về User nếu có token hợp lệ, trả về None nếu là khách (Guest).
    """
    if not credentials or not credentials.credentials:
        return None
    
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None
    
    user_id = payload["sub"]
    stmt = select(User).where(User.id == user_id, User.is_active.is_(True))
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

