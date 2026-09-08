"""
Endpoint Cấu hình Hệ thống (System Configuration API - UC013).
Cung cấp API xem cấu hình đang hoạt động (LLM provider, model, qdrant, quota) và cập nhật tham số vận hành khi có quyền quản trị.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.core.config import settings
from app.core.security import verify_admin_key
from app.schemas.config import SystemConfigResponse, SystemConfigUpdate
from app.services.llm_service import llm_service

router = APIRouter(prefix="/config", tags=["System Configuration (UC013)"])

@router.get("", response_model=SystemConfigResponse)
async def get_system_config():
    """
    UC013: Xem cấu hình hệ thống hiện tại.
    Trả về thông tin môi trường, nhà cung cấp LLM, model mặc định, cờ trạng thái khóa API (không để lộ chuỗi bí mật) và cấu hình Qdrant.
    """
    return SystemConfigResponse(
        project_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.APP_ENV,
        llm_provider=settings.LLM_PROVIDER,
        default_model=settings.DEFAULT_LLM_MODEL,
        has_gemini_key=bool(settings.GEMINI_API_KEY),
        has_openai_key=bool(settings.OPENAI_API_KEY),
        qdrant_host=settings.QDRANT_HOST,
        qdrant_use_memory=settings.QDRANT_USE_MEMORY,
        max_search_papers=settings.MAX_SEARCH_PAPERS,
        max_review_retries=settings.MAX_REVIEW_RETRIES
    )

@router.patch("", response_model=SystemConfigResponse, dependencies=[Depends(verify_admin_key)])
@router.put("", response_model=SystemConfigResponse, dependencies=[Depends(verify_admin_key)])
async def update_system_config(payload: SystemConfigUpdate):
    """
    UC013: Cập nhật động cấu hình hệ thống:
    - Thay đổi LLM Provider (Gemini / OpenAI), Model ID, API Keys, Base URL.
    - Cập nhật số lượng bài báo tối đa khi tìm kiếm và số lần thử lại của ReviewAgent.
    - Tự động khởi tạo lại client LLM trong bộ nhớ để áp dụng ngay lập tức mà không cần khởi động lại máy chủ.
    """
    if payload.llm_provider is not None:
        settings.LLM_PROVIDER = payload.llm_provider
    if payload.default_model is not None:
        settings.DEFAULT_LLM_MODEL = payload.default_model
    if payload.gemini_api_key is not None:
        settings.GEMINI_API_KEY = payload.gemini_api_key
    if payload.openai_api_key is not None:
        settings.OPENAI_API_KEY = payload.openai_api_key
    if payload.openai_base_url is not None:
        settings.OPENAI_BASE_URL = payload.openai_base_url
    if payload.max_search_papers is not None:
        settings.MAX_SEARCH_PAPERS = payload.max_search_papers
    if payload.max_review_retries is not None:
        settings.MAX_REVIEW_RETRIES = payload.max_review_retries

    # Khởi tạo lại các client kết nối LLM theo cấu hình mới
    llm_service.provider = settings.LLM_PROVIDER.lower()
    llm_service.default_model = settings.DEFAULT_LLM_MODEL
    llm_service._init_clients()

    return SystemConfigResponse(
        project_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.APP_ENV,
        llm_provider=settings.LLM_PROVIDER,
        default_model=settings.DEFAULT_LLM_MODEL,
        has_gemini_key=bool(settings.GEMINI_API_KEY),
        has_openai_key=bool(settings.OPENAI_API_KEY),
        qdrant_host=settings.QDRANT_HOST,
        qdrant_use_memory=settings.QDRANT_USE_MEMORY,
        max_search_papers=settings.MAX_SEARCH_PAPERS,
        max_review_retries=settings.MAX_REVIEW_RETRIES
    )

@router.post("/test-llm")
async def test_llm_connection():
    """
    Kiểm tra kết nối trực tiếp với LLM Provider đang cấu hình:
    - Gửi câu hỏi thử nghiệm ngắn gọn tới mô hình.
    - Trả về thông báo thành công cùng phản hồi thực tế từ AI hoặc thông báo lỗi rõ ràng.
    """
    try:
        test_prompt = "Say 'PaperFlow LLM connection is healthy and working!' in exactly 1 sentence."
        response_text = await llm_service.generate_text(test_prompt, temperature=0.0)
        return {
            "status": "ok",
            "message": f"Kết nối {settings.LLM_PROVIDER.upper()} ({settings.DEFAULT_LLM_MODEL}) thành công!",
            "response": response_text.strip()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Lỗi kết nối LLM ({settings.LLM_PROVIDER}): {str(e)}"
        }

