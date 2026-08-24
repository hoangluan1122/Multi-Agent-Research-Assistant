"""
Script khởi chạy trực tiếp máy chủ Uvicorn cho Backend PaperFlow.
Sử dụng cấu hình từ app.core.config.settings.
"""

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    # Khởi chạy Uvicorn server với các cấu hình host, port, reload chế độ debug
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

