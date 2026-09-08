"""
Module quản lý cấu hình tập trung cho toàn bộ ứng dụng PaperFlow.
Sử dụng Pydantic Settings để đọc cấu hình từ biến môi trường hoặc file .env.
"""

import os
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Lớp cấu hình ứng dụng (Application Settings):
    - Cấu hình chung của ứng dụng và máy chủ.
    - Cấu hình danh sách tên miền CORS cho phép truy cập.
    - Cấu hình cơ sở dữ liệu quan hệ (PostgreSQL / SQLite).
    - Cấu hình cơ sở dữ liệu vector Qdrant.
    - Cấu hình kết nối LLM (Gemini, OpenAI, Mock).
    - Cấu hình quy trình phân tích và Multi-Agent.
    """
    # Tìm kiếm file .env tại thư mục Backend, thư mục gốc hoặc thư mục hiện tại
    _backend_env = Path(__file__).resolve().parents[2] / ".env"
    _root_env = Path(__file__).resolve().parents[3] / ".env"
    
    model_config = SettingsConfigDict(
        env_file=[str(_backend_env), str(_root_env), ".env"],
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Cấu hình thông tin ứng dụng
    PROJECT_NAME: str = "PaperFlow - Multi-Agent Research Assistant"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    # Cấu hình bảo mật & JWT Token
    SECRET_KEY: str = "paperflow-super-secure-jwt-secret-key-2026-multi-agent-system"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 ngày
    ALGORITHM: str = "HS256"

    # Cấu hình danh sách Origin được phép truy cập CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Chuẩn hóa chuỗi cấu hình CORS thành mảng các chuỗi URL."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["*"]

    # Cấu hình Database (Mặc định SQLite Async hoặc PostgreSQL nếu có cấu hình)
    DATABASE_URL: str = "sqlite+aiosqlite:///./paperflow.db"

    # Cấu hình Vector Database (Qdrant)
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str = ""
    QDRANT_USE_MEMORY: bool = True  # Sử dụng in-memory Qdrant nếu không có server rời
    QDRANT_COLLECTION_NAME: str = "paperflow_chunks"
    VECTOR_DIMENSION: int = 768  # Kích thước vector embedding chuẩn

    # Cấu hình mô hình ngôn ngữ lớn (LLM Settings)
    LLM_PROVIDER: str = "gemini"  # "gemini", "openai", "mock"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    DEFAULT_LLM_MODEL: str = "gemini-3.7-flash"
    TEMPERATURE: float = 0.2

    # Cấu hình quy trình Multi-Agent & xử lý tài liệu
    MAX_SEARCH_PAPERS: int = 10     # Số lượng bài báo tối đa tìm kiếm mỗi lần
    CHUNK_SIZE: int = 1000          # Độ dài mỗi đoạn văn bản (chunk) khi chia nhỏ PDF
    CHUNK_OVERLAP: int = 150        # Số lượng ký tự chồng lấn giữa các chunk
    MAX_REVIEW_RETRIES: int = 2     # Số lần thử viết lại tối đa nếu thẩm định chưa đạt
    UPLOAD_DIR: str = "./uploads"   # Thư mục lưu trữ tài liệu PDF tải lên


# Khởi tạo đối tượng cấu hình toàn cục
settings = Settings()
# Đảm bảo thư mục upload luôn tồn tại
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

