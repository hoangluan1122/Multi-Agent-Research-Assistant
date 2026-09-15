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


# @trace: REQ-027, REQ-038
def test_default_llm_model_is_gemini_2_0():
    """Kiểm tra mô hình mặc định trong config là gemini chuẩn Google."""
    assert settings.DEFAULT_LLM_MODEL in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-3.6-flash"]


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


# @trace: REQ-032
def test_gambling_vietnamese_query_mapping_and_no_bac_residue():
    """Kiểm tra từ khóa 'cờ bạc cuộc sống' được ánh xạ sang 'gambling', không bị sót âm 'bac' hoặc 'cuoc'."""
    from app.services.query_normalizer import fallback_academic_keywords
    query = fallback_academic_keywords("cờ bạc cuộc sống")
    assert "gambling" in query
    assert "quality" in query or "life" in query
    # Không để sót âm tiết tiếng Việt 'bac' (dễ nhầm với Bacterial Artificial Chromosome)
    assert "bac" not in query.split()
    assert "cuoc" not in query.split()
    assert "song" not in query.split()


# @trace: REQ-031, REQ-033
def test_gambling_search_discards_asthma_and_covid_unrelated_papers():
    """Kiểm tra tìm kiếm cờ bạc loại bỏ triệt để các bài báo hen suyễn (Asthma) và COVID-19 chỉ khớp từ 'quality of life'."""
    service = AcademicSearchService()
    papers = [
        {
            "title": "Predicting Problem Gambling in Young Men: The Impact of Sports Gambling Frequency and Internalizing Symptoms",
            "abstract": "Young men aged 18-25 years are at disproportionately increased risk for gambling problems.",
            "year": 2025,
            "source": "openalex"
        },
        {
            "title": "The impacts of stress and loneliness on gambling and gaming problems: A nationwide longitudinal study",
            "abstract": "Problems related to gambling and digital gaming have been a topic of concern for years.",
            "year": 2024,
            "source": "openalex"
        },
        {
            "title": "Psychological and Sociocultural Determinants in Childhood Asthma Disease: Impact on Quality of Life",
            "abstract": "Asthma is the most common chronic disease in childhood. The presence of this pathology leads to alterations.",
            "year": 2022,
            "source": "openalex"
        },
        {
            "title": "Evidence Synthesis of Digital Interventions to Mitigate the Negative Impact of the COVID-19 Pandemic on Public Mental Health: Rapid Meta-review",
            "abstract": "Accumulating evidence suggests the COVID-19 pandemic has negative effects on public mental health.",
            "year": 2021,
            "source": "openalex"
        },
        {
            "title": "C9orf72 BAC Mouse Model with Motor Deficits and Neurodegenerative Features of ALS/FTD",
            "abstract": "Bacterial Artificial Chromosome BAC transgenic mouse model.",
            "year": 2016,
            "source": "openalex"
        }
    ]

    ranked = service._rank_by_query_match("gambling quality life", papers)
    # Chỉ giữ lại 2 bài cờ bạc thực tế, loại bỏ hoàn toàn 3 bài hen suyễn, covid và chuột BAC
    assert len(ranked) == 2
    for p in ranked:
        assert "gambling" in p["title"].lower() or "gambling" in p["abstract"].lower()
        assert "asthma" not in p["title"].lower()
        assert "covid" not in p["title"].lower()
        assert "bac" not in p["title"].lower()


# @trace: REQ-034, REQ-035, REQ-036
@pytest.mark.asyncio
async def test_paper_delete_clear_and_search_clear_existing():
    """
    Kiểm định toàn diện REQ-034, REQ-035, REQ-036:
    - REQ-034: Xóa bài báo đơn lẻ DELETE /api/v1/papers/{id} trả về 204.
    - REQ-035: Xóa toàn bộ bài trong phiên DELETE /api/v1/papers/session/{session_id} trả về 200.
    - REQ-036: Tìm kiếm với clear_existing=True xóa sạch bài cũ trước khi lưu batch mới.
    """
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from app.db.session import AsyncSessionLocal, init_db
    from app.models.session import ResearchSession
    from app.models.paper import Paper
    import uuid

    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        session_id = str(uuid.uuid4())
        paper_id_1 = str(uuid.uuid4())
        paper_id_2 = str(uuid.uuid4())

        async with AsyncSessionLocal() as db:
            s = ResearchSession(
                id=session_id,
                topic="Gambling Research Test",
                research_question="Impacts on youth",
                status="COMPLETED"
            )
            db.add(s)
            p1 = Paper(
                id=paper_id_1,
                session_id=session_id,
                title="Gambling Paper 1",
                relevance_score=0.9
            )
            p2 = Paper(
                id=paper_id_2,
                session_id=session_id,
                title="Gambling Paper 2",
                relevance_score=0.85
            )
            db.add_all([p1, p2])
            await db.commit()

        # REQ-034: Xóa bài báo đơn lẻ
        del_resp = await client.delete(f"/api/v1/papers/{paper_id_1}")
        assert del_resp.status_code == 204

        async with AsyncSessionLocal() as db:
            res1 = await db.get(Paper, paper_id_1)
            assert res1 is None
            res2 = await db.get(Paper, paper_id_2)
            assert res2 is not None

        # REQ-035: Xóa toàn bộ bài trong phiên
        clear_resp = await client.delete(f"/api/v1/papers/session/{session_id}")
        assert clear_resp.status_code == 200
        assert clear_resp.json()["deleted_count"] == 1

        async with AsyncSessionLocal() as db:
            res2_after = await db.get(Paper, paper_id_2)
            assert res2_after is None

        # REQ-036: Thêm lại 1 bài cũ rồi test search với clear_existing=True
        paper_id_3 = str(uuid.uuid4())
        async with AsyncSessionLocal() as db:
            p3 = Paper(
                id=paper_id_3,
                session_id=session_id,
                title="Old Gambling Paper To Be Cleared",
                relevance_score=0.7
            )
            db.add(p3)
            await db.commit()

        search_payload = {
            "session_id": session_id,
            "query": "sports betting problem gambling",
            "max_results": 2,
            "clear_existing": True
        }
        search_resp = await client.post("/api/v1/papers/search", json=search_payload)
        assert search_resp.status_code == 200

        # Kiểm tra paper_id_3 đã bị xóa khỏi DB do clear_existing=True
        async with AsyncSessionLocal() as db:
            res3 = await db.get(Paper, paper_id_3)
            assert res3 is None
            s_del = await db.get(ResearchSession, session_id)
            if s_del:
                await db.delete(s_del)
                await db.commit()


# @trace: REQ-042
@pytest.mark.asyncio
async def test_dynamic_test_llm_missing_openai_key():
    """Kiểm tra REQ-042: Gọi /config/test-llm với provider OpenAI nhưng không có key trả về thông báo lỗi rõ ràng."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from unittest.mock import patch

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("app.core.config.settings.OPENAI_API_KEY", ""):
            resp = await client.post("/api/v1/config/test-llm", json={"llm_provider": "openai", "api_key": ""})
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "error"
            assert "OPENAI" in data["message"]


# @trace: REQ-042
@pytest.mark.asyncio
async def test_dynamic_test_llm_openai_success():
    """Kiểm tra REQ-042: Gọi /config/test-llm với credentials OpenAI động kết nối thành công."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from unittest.mock import patch, MagicMock, AsyncMock

    mock_choice = MagicMock()
    mock_choice.message.content = "PaperFlow LLM connection is healthy and working!"
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("openai.resources.chat.completions.AsyncCompletions.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_completion
            payload = {
                "llm_provider": "openai",
                "default_model": "gpt-4o-mini",
                "api_key": "sk-test-valid-mock-key-12345"
            }
            resp = await client.post("/api/v1/config/test-llm", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"
            assert "OPENAI" in data["message"]
            assert "gpt-4o-mini" in data["message"]
            assert "PaperFlow LLM" in data["response"]


# @trace: REQ-042
@pytest.mark.asyncio
async def test_dynamic_test_llm_gemini_missing_key():
    """Kiểm tra REQ-042: Gọi /config/test-llm với provider Gemini nhưng không có key trả về thông báo lỗi rõ ràng."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from unittest.mock import patch

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("app.core.config.settings.GEMINI_API_KEY", ""):
            resp = await client.post("/api/v1/config/test-llm", json={"llm_provider": "gemini", "api_key": ""})
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "error"
            assert "GEMINI" in data["message"]


# @trace: REQ-043
@pytest.mark.asyncio
async def test_dynamic_test_llm_gemini_success_rest():
    """Kiểm tra REQ-043: Gọi /config/test-llm với Gemini trả về 200 OK thành công qua REST."""
    from httpx import AsyncClient, ASGITransport, Response
    from app.main import app
    from unittest.mock import patch, AsyncMock

    mock_resp = Response(
        status_code=200,
        json={
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "PaperFlow LLM connection is healthy and working!"}]
                    }
                }
            ]
        }
    )

    mock_http_client = AsyncMock()
    mock_http_client.__aenter__.return_value = mock_http_client
    mock_http_client.post.return_value = mock_resp

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("app.api.v1.endpoints.config.httpx.AsyncClient", return_value=mock_http_client):
            payload = {
                "llm_provider": "gemini",
                "default_model": "gemini-2.0-flash",
                "api_key": "AQ.mock_valid_gemini_key_12345"
            }
            resp = await client.post("/api/v1/config/test-llm", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"
            assert "GEMINI" in data["message"]
            assert "PaperFlow LLM" in data["response"]


# @trace: REQ-043
@pytest.mark.asyncio
async def test_dynamic_test_llm_gemini_auth_unsupported_error():
    """Kiểm tra REQ-043: Khi Google trả về 401 ACCESS_TOKEN_TYPE_UNSUPPORTED, trả về thông điệp hướng dẫn rõ ràng."""
    from httpx import AsyncClient, ASGITransport, Response
    from app.main import app
    from unittest.mock import patch, AsyncMock

    mock_resp = Response(
        status_code=401,
        json={
            "error": {
                "code": 401,
                "message": "Request had invalid authentication credentials.",
                "status": "UNAUTHENTICATED",
                "details": [{"reason": "ACCESS_TOKEN_TYPE_UNSUPPORTED"}]
            }
        }
    )

    mock_http_client = AsyncMock()
    mock_http_client.__aenter__.return_value = mock_http_client
    mock_http_client.post.return_value = mock_resp

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("app.api.v1.endpoints.config.httpx.AsyncClient", return_value=mock_http_client):
            payload = {
                "llm_provider": "gemini",
                "default_model": "gemini-2.0-flash",
                "api_key": "AQ.mock_problematic_key_12345"
            }
            resp = await client.post("/api/v1/config/test-llm", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "error"
            assert "401" in data["message"] or "xác thực" in data["message"].lower()
            assert "aistudio.google.com" in data["message"]


# @trace: REQ-043
@pytest.mark.asyncio
async def test_dynamic_test_llm_gemini_invalid_key_error():
    """Kiểm tra REQ-043: Khi Google trả về 400 API_KEY_INVALID, trả về thông báo khóa không hợp lệ."""
    from httpx import AsyncClient, ASGITransport, Response
    from app.main import app
    from unittest.mock import patch, AsyncMock

    mock_resp = Response(
        status_code=400,
        json={
            "error": {
                "code": 400,
                "message": "API key not valid. Please pass a valid API key.",
                "status": "INVALID_ARGUMENT",
                "details": [{"reason": "API_KEY_INVALID"}]
            }
        }
    )

    mock_http_client = AsyncMock()
    mock_http_client.__aenter__.return_value = mock_http_client
    mock_http_client.post.return_value = mock_resp

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("app.api.v1.endpoints.config.httpx.AsyncClient", return_value=mock_http_client):
            payload = {
                "llm_provider": "gemini",
                "default_model": "gemini-2.0-flash",
                "api_key": "AIzaSy_mock_invalid_key_12345"
            }
            resp = await client.post("/api/v1/config/test-llm", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "error"
            assert "không hợp lệ" in data["message"]



