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
    DEBUG: bool = True
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

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, v):
        """Cho phép dùng các giá trị môi trường như release/prod/dev cho DEBUG."""
        if isinstance(v, str):
            normalized = v.strip().lower()
            if normalized in {"release", "production", "prod", "false", "0", "no", "off"}:
                return False
            if normalized in {"debug", "development", "dev", "true", "1", "yes", "on"}:
                return True
        return v

    # Cấu hình Database (Mặc định kết nối Neon Serverless PostgreSQL trên Cloud)
    DATABASE_URL: str = "postgresql+asyncpg://neondb_owner:npg_GSbBip3oC8kf@ep-cool-dust-b3jpkf3f.c-4.ap-southeast-1.aws.neon.tech/neondb?ssl=require"

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

    # Cấu hình tìm kiếm học thuật bên ngoài (OpenAlex, arXiv, Semantic Scholar)
    SEMANTIC_SCHOLAR_API_KEY: str = ""
    ACADEMIC_SEARCH_TIMEOUT_SECONDS: float = 30.0
    ACADEMIC_SEARCH_MAX_RETRIES: int = 2
    ACADEMIC_SEARCH_TRUST_ENV: bool = False
    ACADEMIC_SEARCH_USER_AGENT: str = "PaperFlow/1.0 Multi-Agent Research Assistant"
    ACADEMIC_SEARCH_OPENALEX_FALLBACK: bool = True
    ACADEMIC_SEARCH_CACHE_TTL_SECONDS: int = 900
    ACADEMIC_SEARCH_CACHE_MAX_ENTRIES: int = 128
    ACADEMIC_SEARCH_CANDIDATE_MULTIPLIER: int = 4
    ACADEMIC_SEARCH_MIN_CANDIDATES_PER_SOURCE: int = 30
    ACADEMIC_SEARCH_MAX_CANDIDATES_PER_SOURCE: int = 40
    ACADEMIC_SEARCH_MIN_RELEVANCE_SCORE: float = 0.45
    ARXIV_MIN_REQUEST_INTERVAL_SECONDS: float = 3.2
    SEMANTIC_SCHOLAR_MIN_REQUEST_INTERVAL_SECONDS: float = 1.1
    OPENALEX_MIN_REQUEST_INTERVAL_SECONDS: float = 0.2
    OPENALEX_API_KEY: str = ""

    # Cấu hình quy trình Multi-Agent & xử lý tài liệu
    MAX_SEARCH_PAPERS: int = 10     # Số lượng bài báo tối đa tìm kiếm mỗi lần
    CHUNK_SIZE: int = 1000          # Độ dài mỗi đoạn văn bản (chunk) khi chia nhỏ PDF
    CHUNK_OVERLAP: int = 150        # Số lượng ký tự chồng lấn giữa các chunk
    MAX_REVIEW_RETRIES: int = 2     # Số lần thử viết lại tối đa nếu thẩm định chưa đạt
    UPLOAD_DIR: str = "./uploads"   # Thư mục lưu trữ tài liệu PDF tải lên

    # @trace: REQ-008
    GUEST_MAX_SESSIONS: int = 2     # Số lượt nghiên cứu tối đa dành cho khách vãng lai


# Khởi tạo đối tượng cấu hình toàn cục
settings = Settings()
# Đảm bảo thư mục upload luôn tồn tại
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

