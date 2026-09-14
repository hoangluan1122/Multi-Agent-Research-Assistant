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

# @trace: REQ-012: Lưu trữ cấu hình mặc định ban đầu từ môi trường máy chủ
_SYSTEM_DEFAULT_GEMINI_KEY = settings.GEMINI_API_KEY
_SYSTEM_DEFAULT_OPENAI_KEY = settings.OPENAI_API_KEY
_SYSTEM_DEFAULT_OPENAI_BASE_URL = settings.OPENAI_BASE_URL
_SYSTEM_DEFAULT_PROVIDER = settings.LLM_PROVIDER
_SYSTEM_DEFAULT_MODEL = settings.DEFAULT_LLM_MODEL
_is_using_custom_key = False

# @trace: REQ-012
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
        has_semantic_scholar_key=bool(settings.SEMANTIC_SCHOLAR_API_KEY),
        has_openalex_key=bool(settings.OPENALEX_API_KEY),
        qdrant_host=settings.QDRANT_HOST,
        qdrant_use_memory=settings.QDRANT_USE_MEMORY,
        max_search_papers=settings.MAX_SEARCH_PAPERS,
        max_review_retries=settings.MAX_REVIEW_RETRIES,
        use_system_key=not _is_using_custom_key
    )

# @trace: REQ-011, REQ-012
@router.patch("", response_model=SystemConfigResponse, dependencies=[Depends(verify_admin_key)])
@router.put("", response_model=SystemConfigResponse, dependencies=[Depends(verify_admin_key)])
async def update_system_config(payload: SystemConfigUpdate):
    """
    UC013: Cập nhật động cấu hình hệ thống:
    - Chuyển đổi giữa API có sẵn của Web và API cá nhân tự thêm (REQ-012).
    - Thay đổi LLM Provider (Gemini / OpenAI / Groq / OpenRouter), Model ID, API Keys, Base URL.
    - Cập nhật số lượng bài báo tối đa khi tìm kiếm và số lần thử lại của ReviewAgent.
    - Tự động khởi tạo lại client LLM trong bộ nhớ để áp dụng ngay lập tức mà không cần khởi động lại máy chủ.
    """
    global _is_using_custom_key

    if payload.use_system_default:
        # Khôi phục về khóa API và cấu hình mặc định của hệ thống
        settings.GEMINI_API_KEY = _SYSTEM_DEFAULT_GEMINI_KEY
        settings.OPENAI_API_KEY = _SYSTEM_DEFAULT_OPENAI_KEY
        settings.OPENAI_BASE_URL = _SYSTEM_DEFAULT_OPENAI_BASE_URL
        if payload.llm_provider:
            settings.LLM_PROVIDER = payload.llm_provider
        else:
            settings.LLM_PROVIDER = _SYSTEM_DEFAULT_PROVIDER
        if payload.default_model:
            settings.DEFAULT_LLM_MODEL = payload.default_model
        else:
            settings.DEFAULT_LLM_MODEL = _SYSTEM_DEFAULT_MODEL
        _is_using_custom_key = False
    else:
        if payload.gemini_api_key or payload.openai_api_key:
            _is_using_custom_key = True
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

    if payload.semantic_scholar_api_key is not None:
        settings.SEMANTIC_SCHOLAR_API_KEY = payload.semantic_scholar_api_key
    if payload.openalex_api_key is not None:
        settings.OPENALEX_API_KEY = payload.openalex_api_key
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
        has_semantic_scholar_key=bool(settings.SEMANTIC_SCHOLAR_API_KEY),
        has_openalex_key=bool(settings.OPENALEX_API_KEY),
        qdrant_host=settings.QDRANT_HOST,
        qdrant_use_memory=settings.QDRANT_USE_MEMORY,
        max_search_papers=settings.MAX_SEARCH_PAPERS,
        max_review_retries=settings.MAX_REVIEW_RETRIES,
        use_system_key=not _is_using_custom_key
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

