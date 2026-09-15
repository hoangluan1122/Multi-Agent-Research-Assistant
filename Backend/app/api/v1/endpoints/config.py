"""
Endpoint Cấu hình Hệ thống (System Configuration API - UC013).
Cung cấp API xem cấu hình đang hoạt động (LLM provider, model, qdrant, quota) và cập nhật tham số vận hành khi có quyền quản trị.
"""

import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from app.core.config import settings
from app.core.security import verify_admin_key
from app.schemas.config import SystemConfigResponse, SystemConfigUpdate, TestLlmRequest
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

# @trace: REQ-041, REQ-042
@router.post("/test-llm")
async def test_llm_connection(payload: Optional[TestLlmRequest] = Body(default=None)):
    """
    Kiểm tra kết nối trực tiếp với LLM Provider (REQ-041, REQ-042):
    - Hỗ trợ kiểm tra động (in-flight) các tham số được gửi lên từ form Cài Đặt (provider, model, API key, base_url)
      mà không bắt buộc người dùng phải nhấn 'Lưu' trước.
    - Nếu không gửi payload, sử dụng cấu hình đang hoạt động trên hệ thống.
    - Gửi câu hỏi thử nghiệm ngắn gọn tới mô hình thật (allow_mock=False).
    - Trả về thông báo thành công cùng phản hồi thực tế từ AI hoặc thông báo lỗi rõ ràng.
    """
    target_provider = (payload.llm_provider.strip().lower() if (payload and payload.llm_provider) else settings.LLM_PROVIDER.lower())
    target_model = (payload.default_model.strip() if (payload and payload.default_model) else settings.DEFAULT_LLM_MODEL)
    custom_key = (payload.api_key.strip() if (payload and payload.api_key) else None)
    custom_base_url = (payload.base_url.strip() if (payload and payload.base_url) else None)
    test_prompt = "Say 'PaperFlow LLM connection is healthy and working!' in exactly 1 sentence."

    # Trường hợp 1: Provider là OpenAI hoặc OpenAI-compatible (Groq, OpenRouter...)
    if target_provider != "gemini":
        api_key = custom_key or (settings.OPENAI_API_KEY.strip() if settings.OPENAI_API_KEY else "")
        base_url = custom_base_url or settings.OPENAI_BASE_URL
        if not api_key or api_key.startswith("your_"):
            return {
                "status": "error",
                "message": f"Lỗi kết nối LLM ({target_provider}): Khóa API {target_provider.upper()} chưa được nhập hoặc chưa cấu hình trên hệ thống."
            }
        # @trace: REQ-042: Cảnh báo người dùng nếu nhập nhầm khóa của Google Gemini sang OpenAI
        if target_provider == "openai" and (api_key.startswith("AQ.") or api_key.startswith("AIza")):
            return {
                "status": "error",
                "message": "Lỗi kết nối LLM (openai): Khóa API bạn nhập có định dạng của Google Gemini (bắt đầu bằng 'AQ.' hoặc 'AIza'). Vui lòng chọn thẻ 'Google Gemini' ở trên hoặc nhập khóa OpenAI hợp lệ (bắt đầu bằng 'sk-')."
            }
        http_client = None
        try:
            import httpx
            from openai import AsyncOpenAI
            # @trace: REQ-042: Khởi tạo httpx.AsyncClient tường minh để tương thích 100% với httpx >= 0.28.0, tránh lỗi proxies kwarg
            http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(20.0, connect=10.0),
                follow_redirects=True
            )
            temp_openai = AsyncOpenAI(api_key=api_key, base_url=base_url, http_client=http_client)
            chosen_model = target_model if target_model else ("gpt-4o-mini" if target_provider == "openai" else "llama-3.3-70b-versatile")
            response = await asyncio.wait_for(
                temp_openai.chat.completions.create(
                    model=chosen_model,
                    messages=[{"role": "user", "content": test_prompt}],
                    temperature=0.0
                ),
                timeout=20.0
            )
            text = response.choices[0].message.content or ""
            return {
                "status": "ok",
                "message": f"Kết nối {target_provider.upper()} ({chosen_model}) thành công!",
                "response": text.strip()
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Lỗi kết nối LLM ({target_provider}): {str(e)}"
            }
        finally:
            if http_client:
                await http_client.aclose()

    # Trường hợp 2: Provider là Google Gemini
    api_key = custom_key or (settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else "")
    if not api_key or api_key.startswith("your_") or len(api_key) < 15:
        return {
            "status": "error",
            "message": "Lỗi kết nối LLM (gemini): Khóa GEMINI_API_KEY chưa được nhập hoặc chưa cấu hình trên hệ thống."
        }
    # @trace: REQ-042: Cảnh báo nếu người dùng nhập nhầm khóa OpenAI sang Gemini
    if api_key.startswith("sk-"):
        return {
            "status": "error",
            "message": "Lỗi kết nối LLM (gemini): Khóa API bạn nhập có định dạng của OpenAI (bắt đầu bằng 'sk-'). Vui lòng chọn thẻ 'OpenAI' ở trên hoặc nhập khóa Google Gemini hợp lệ (lấy từ Google AI Studio)."
        }

    clean_target = target_model
    if clean_target and (clean_target.startswith("gemini-3.") or clean_target.startswith("gemini-2.5")):
        clean_target = "gemini-2.0-flash"
    candidate_models = [clean_target, "gemini-2.0-flash", "gemini-1.5-flash"]
    models_to_try = list(dict.fromkeys([m for m in candidate_models if m]))
    last_err = None

    # Thử gọi google-genai SDK
    try:
        from google import genai
        from google.genai import types
        temp_client = genai.Client(api_key=api_key)
        for m_name in models_to_try:
            try:
                config = types.GenerateContentConfig(temperature=0.0)
                response = await asyncio.wait_for(
                    temp_client.aio.models.generate_content(
                        model=m_name,
                        contents=test_prompt,
                        config=config
                    ),
                    timeout=20.0
                )
                if response and response.text:
                    return {
                        "status": "ok",
                        "message": f"Kết nối GEMINI ({m_name}) thành công!",
                        "response": response.text.strip()
                    }
            except Exception as e:
                err_str = str(e)
                last_err = err_str
                # Nếu API key không hợp lệ hoặc bị vô hiệu hóa, thông báo ngay lập tức
                if "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
                    return {
                        "status": "error",
                        "message": "Lỗi kết nối LLM (gemini): Khóa API Google Gemini không hợp lệ hoặc đã bị vô hiệu hóa. Vui lòng kiểm tra lại khóa API được cấp từ https://aistudio.google.com/app/apikey."
                    }
                # Nếu tài khoản bị cạn kiệt hạn mức quota
                if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                    return {
                        "status": "error",
                        "message": "Lỗi kết nối LLM (gemini): Khóa Google Gemini này đã hết hạn mức (Quota limit 429). Vui lòng thử lại sau vài phút hoặc tạo API Key mới trên tài khoản Google khác."
                    }
                continue
    except Exception as e:
        last_err = str(e)

    # Thử qua legacy google.generativeai nếu có
    try:
        import google.generativeai as gai
        gai.configure(api_key=api_key)
        for m_name in ["gemini-2.0-flash", "gemini-1.5-flash"]:
            try:
                g_model = gai.GenerativeModel(model_name=m_name)
                response = await asyncio.to_thread(
                    g_model.generate_content,
                    test_prompt,
                    generation_config={"temperature": 0.0}
                )
                if response and response.text:
                    return {
                        "status": "ok",
                        "message": f"Kết nối GEMINI ({m_name}) thành công!",
                        "response": response.text.strip()
                    }
            except Exception as e:
                err_str = str(e)
                last_err = err_str
                if "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
                    return {
                        "status": "error",
                        "message": "Lỗi kết nối LLM (gemini): Khóa API Google Gemini không hợp lệ hoặc đã bị vô hiệu hóa. Vui lòng kiểm tra lại khóa API được cấp từ https://aistudio.google.com/app/apikey."
                    }
                if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                    return {
                        "status": "error",
                        "message": "Lỗi kết nối LLM (gemini): Khóa Google Gemini này đã hết hạn mức (Quota limit 429). Vui lòng thử lại sau vài phút hoặc tạo API Key mới trên tài khoản Google khác."
                    }
                continue
    except Exception as e:
        last_err = str(e)

    return {
        "status": "error",
        "message": f"Lỗi kết nối LLM (gemini): {last_err or 'Không thể kết nối tới Google Gemini API'}"
    }

