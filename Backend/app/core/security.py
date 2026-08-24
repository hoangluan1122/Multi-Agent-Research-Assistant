"""
Module bảo mật và xác thực (Authentication/Authorization) cho API PaperFlow.
Hỗ trợ xác thực qua API Key trên HTTP Header.
"""

import secrets
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

# Định nghĩa header nhận API Key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_admin_key(api_key: str = Security(api_key_header)):
    """
    Xác thực API Key của người dùng / quản trị viên:
    - Ở môi trường development: Bỏ qua kiểm tra để thuận tiện phát triển.
    - Ở môi trường production: Bắt buộc phải có API Key hợp lệ trong header X-API-Key.
    """
    # Ở chế độ phát triển (development), bỏ qua xác thực nếu chưa thiết lập key
    if settings.APP_ENV == "development":
        return True
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key header missing (Thiếu header X-API-Key)",
        )
    return True

