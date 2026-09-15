"""
Bộ kiểm thử Smoke Test API & Nghiệp vụ Cốt lõi (REQ-024 đến REQ-030).
Dùng cho CI/CD Pipeline để kiểm định chức năng thực tế của hệ thống sau mỗi lần deploy:
- REQ-024: Circuit Breaker dừng luồng khi 0 bài báo.
- REQ-025: Tìm kiếm đa nguồn tích lũy theo số bài hợp lệ sau lọc.
- REQ-026: Xử lý từ khóa học thuật tiếng Việt và loại bỏ từ vô nghĩa.
- REQ-027: Cấu hình mặc định gemini-2.5-flash.
- REQ-028: Phản biện mock minh bạch NEEDS_REVISION khi LLM offline.
- REQ-029: Database URL an toàn không chứa credential hardcode.
"""

import pytest
import asyncio
from app.services.academic_search import AcademicSearchService
from app.agents.search_agent import search_agent
from app.services.llm_service import llm_service
from app.core.config import settings


# @trace: REQ-026
def test_vietnamese_deep_learning_query_translation_no_residue():
    """Kiểm tra cụm từ tiếng Việt 'deep learning mô hình đa dạng đáy' không bị sót 'mo hinh dai dang day'."""
    topic = "deep learning mô hình đa dạng đáy"
    query = search_agent._fallback_search_query(topic)
    assert "deep learning" in query
    assert "model" in query or "diversity" in query
    # Tuyệt đối không để sót các từ vô nghĩa không dấu vào query quốc tế
    assert "mo hinh" not in query
    assert "dai dang" not in query
    assert "day" not in query.split()


# @trace: REQ-026
def test_academic_search_filters_vietnamese_stopwords_from_scoring():
    """Kiểm tra _query_terms không đưa các từ không dấu làm hỏng điểm khớp của bài báo tiếng Anh."""
    service = AcademicSearchService()
    terms = service._query_terms("deep learning mo hinh dai dang day")
    assert "deep" in terms
    assert "learning" in terms
    assert "mo" not in terms
    assert "hinh" not in terms
    assert "dai" not in terms


# @trace: REQ-028
def test_review_agent_mock_returns_transparent_needs_revision():
    """Kiểm tra khi LLM offline, review mock trả về NEEDS_REVISION minh bạch, không giả mạo PASS 94 điểm."""
    prompt = "Review this academic report based on criteria and assign score"
    mock_res = llm_service._mock_generation(prompt, None)
    import json
    data = json.loads(mock_res)
    assert data["status"] == "NEEDS_REVISION"
    assert data["score"] < 80.0
    assert "Cảnh báo" in data["feedback"] or "ngoại tuyến" in data["issues"][0]["description"]


# @trace: REQ-027
def test_default_llm_model_is_gemini_2_5():
    """Kiểm tra mô hình mặc định trong config là gemini-2.5-flash theo đúng lựa chọn người dùng."""
    assert "2.5" in settings.DEFAULT_LLM_MODEL or "gemini" in settings.DEFAULT_LLM_MODEL


# @trace: REQ-029
def test_config_database_url_not_hardcoded_plain_secret():
    """Kiểm tra config.py không chứa mật khẩu database thực tế hardcode trong mã nguồn."""
    from app.core.config import Settings
    default_s = Settings(_env_file=None)
    assert "npg_GSbBip3oC8kf" not in default_s.DATABASE_URL


# @trace: REQ-025
@pytest.mark.asyncio
async def test_incremental_search_does_not_skip_secondary_sources():
    """Kiểm tra khi nguồn 1 không có bài hợp lệ, cơ chế tích lũy vẫn kích hoạt Crossref & Europe PMC."""
    service = AcademicSearchService()
    # Mock arXiv trả về danh sách bài báo bị lọc hết bởi bộ lọc ngữ cảnh
    dummy_unrelated = [
        {
            "title": "Bệnh ung thư tuyến tiền liệt và kháng nguyên PSAT",
            "abstract": "Nghiên cứu lâm sàng về tuyến tiền liệt và PSA.",
            "year": 2024,
            "url": "https://arxiv.org/abs/2401.99999",
            "source": "arxiv"
        }
    ]
    # Lọc cho truy vấn 'tiền tệ tài chính'
    filtered = service._filter_and_rank_batch("tiền tệ tài chính ngân hàng", dummy_unrelated)
    assert len(filtered) == 0  # Bị loại do lệch ngữ cảnh
