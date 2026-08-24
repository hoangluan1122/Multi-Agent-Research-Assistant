"""
Pydantic Schemas cấu hình hệ thống (System Config).
Định nghĩa cấu trúc thông tin cấu hình runtime, trạng thái API key và cập nhật tham số hệ thống.
"""

from typing import Optional, List
from pydantic import BaseModel

class SystemConfigResponse(BaseModel):
    """Schema dữ liệu trả về thông tin cấu hình hiện tại của hệ thống (ẩn các API key nhạy cảm)."""
    project_name: str
    version: str
    environment: str
    llm_provider: str
    default_model: str
    has_gemini_key: bool
    has_openai_key: bool
    qdrant_host: str
    qdrant_use_memory: bool
    max_search_papers: int
    max_review_retries: int

class SystemConfigUpdate(BaseModel):
    """Schema dữ liệu cập nhật cấu hình hệ thống động trong lúc chạy."""
    llm_provider: Optional[str] = None
    default_model: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    max_search_papers: Optional[int] = None
    max_review_retries: Optional[int] = None

