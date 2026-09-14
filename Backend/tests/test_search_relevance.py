import asyncio
import json
from unittest.mock import AsyncMock
import httpx

from app.core.config import Settings
from app.agents.search_agent import SearchAgent
from app.services.academic_search import (
    AcademicSearchError,
    AcademicSearchService,
    AcademicSearchSourceError,
)
from app.services.llm_service import LLMService, llm_service


def test_mock_keyword_extraction_uses_requested_topic():
    service = LLMService()
    prompt = (
        "Given this research topic or question: 'Intelligent Agent', "
        "extract 3-5 concise academic search keywords (English) for searching academic papers."
    )

    keywords = service._mock_keyword_extraction(prompt)

    assert keywords == "intelligent agent"
    assert "transformer deep learning medical segmentation" not in keywords


def test_mock_keyword_extraction_translates_common_vietnamese_terms():
    service = LLMService()
    prompt = (
        "Given this research topic or question: 'Tác hại của ma túy đối với học sinh', "
        "extract 3-5 concise academic search keywords (English) for searching academic papers."
    )

    keywords = service._mock_keyword_extraction(prompt)

    assert "drug" in keywords
    assert "abuse" in keywords
    assert "students" in keywords
    assert "ma" not in keywords.split()


def test_search_agent_optimizer_uses_keyword_fallback_for_vietnamese_topic(monkeypatch):
    monkeypatch.setattr(llm_service, "genai_client", None)
    monkeypatch.setattr(llm_service, "openai_client", None)

    query = asyncio.run(
        SearchAgent()._optimize_search_query("Tác hại của ma túy đối với học sinh")
    )

    assert "drug" in query
    assert "students" in query
    assert "method" not in query.lower()
    assert "dataset" not in query.lower()


def test_mock_translation_preserves_requested_paper_metadata():
    service = LLMService()
    prompt = (
        "Translate this academic paper title and abstract into Vietnamese (Tiếng Việt):\n"
        "Title: Graph Neural Networks for Recommender Systems\n"
        "Abstract: This paper studies graph neural recommendation models.\n"
        "Respond in JSON:\n"
        '{"title_vi": "...", "abstract_vi": "..."}'
    )

    translated = json.loads(service._mock_generation(prompt, None))

    assert translated["title_vi"] == "Graph Neural Networks for Recommender Systems"
    assert translated["abstract_vi"] == "This paper studies graph neural recommendation models."
    assert "Transformer" not in translated["title_vi"]


def test_mock_translation_not_confused_by_extract_word_in_abstract():
    service = LLMService()
    prompt = (
        "Translate this academic paper title and abstract into Vietnamese (Tiếng Việt):\n"
        "Title: Substance Use Prevention for Students\n"
        "Abstract: This paper extracts evidence from school-based prevention studies.\n"
        "Respond in JSON:\n"
        '{"title_vi": "...", "abstract_vi": "..."}'
    )

    translated = json.loads(service._mock_generation(prompt, None))

    assert translated["title_vi"] == "Substance Use Prevention for Students"
    assert translated["abstract_vi"] == "This paper extracts evidence from school-based prevention studies."


def test_settings_accept_release_as_debug_false():
    settings = Settings(DEBUG="release")

    assert settings.DEBUG is False


def test_semantic_scholar_headers_include_configured_api_key(monkeypatch):
    service = AcademicSearchService()
    monkeypatch.setattr(
        "app.services.academic_search.settings.SEMANTIC_SCHOLAR_API_KEY",
        "s2-test-key",
    )

    headers = service._headers_for_source("semantic_scholar")

    assert headers["x-api-key"] == "s2-test-key"


def test_academic_search_http_client_ignores_proxy_env_by_default(monkeypatch):
    captured_kwargs = {}

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            captured_kwargs.update(kwargs)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, **kwargs):
            request = httpx.Request("GET", url)
            return httpx.Response(200, text="ok", request=request)

    monkeypatch.setattr("app.services.academic_search.httpx.AsyncClient", FakeAsyncClient)

    service = AcademicSearchService()
    asyncio.run(
        service._get_with_retry(
            "Test Source",
            "https://example.test/search",
            params={"query": "agent"},
            headers={},
        )
    )

    assert captured_kwargs["trust_env"] is False


def test_arxiv_min_interval_uses_provider_rate_limit_setting(monkeypatch):
    service = AcademicSearchService()
    monkeypatch.setattr(
        "app.services.academic_search.settings.ARXIV_MIN_REQUEST_INTERVAL_SECONDS",
        3.2,
    )

    assert service._min_interval_for_source("arxiv") == 3.2


def test_arxiv_non_200_response_raises_source_error():
    service = AcademicSearchService()
    request = httpx.Request("GET", service.arxiv_base_url)
    service._get_with_retry = AsyncMock(
        return_value=httpx.Response(429, text="Rate exceeded", request=request)
    )

    try:
        asyncio.run(service._search_arxiv("Intelligent Agent", max_results=3))
    except AcademicSearchSourceError as exc:
        assert exc.status_code == 429
        assert "ArXiv" in str(exc)
    else:
        raise AssertionError("Expected AcademicSearchSourceError for non-200 arXiv response")


def test_query_relevance_filter_removes_unrelated_papers():
    service = AcademicSearchService()
    papers = [
        {
            "title": "Intelligent Agents for Autonomous Research Planning",
            "abstract": "A framework for intelligent agent decision making and planning.",
            "year": 2024,
            "relevance_score": 0.9,
        },
        {
            "title": "Empirical Evaluation of Transformer Medical Image Segmentation",
            "abstract": "A benchmark of transformer architectures for medical segmentation.",
            "year": 2024,
            "relevance_score": 0.95,
        },
    ]

    ranked = service._rank_by_query_match("Intelligent Agent", papers)

    assert [paper["title"] for paper in ranked] == [
        "Intelligent Agents for Autonomous Research Planning"
    ]
    assert ranked[0]["relevance_score"] > 0.8


def test_query_relevance_requires_both_terms_for_short_queries():
    service = AcademicSearchService()
    papers = [
        {
            "title": "Drug Discovery with Graph Neural Networks",
            "abstract": "A benchmark for molecular property prediction.",
            "year": 2024,
            "relevance_score": 0.9,
        }
    ]

    assert service._rank_by_query_match("drug abuse", papers) == []


def test_query_relevance_matches_synonymous_academic_terms():
    service = AcademicSearchService()
    papers = [
        {
            "title": "Substance Use Disorder Among Adolescents",
            "abstract": "A study of addiction prevention and treatment outcomes.",
            "year": 2024,
            "relevance_score": 0.9,
        }
    ]

    ranked = service._rank_by_query_match("drug abuse", papers)

    assert len(ranked) == 1
    assert ranked[0]["title"] == "Substance Use Disorder Among Adolescents"


def test_arxiv_query_applies_all_prefix_to_each_term():
    service = AcademicSearchService()

    query = service._build_arxiv_query("medical image segmentation transformer")

    assert query == "all:medical AND all:image AND all:segmentation AND all:transformer"


def test_search_returns_empty_when_sources_have_no_results():
    service = AcademicSearchService()
    service._search_arxiv = AsyncMock(return_value=[])
    service._search_semantic_scholar = AsyncMock(return_value=[])
    service._search_openalex = AsyncMock(return_value=[])

    results = asyncio.run(service.search("Intelligent Agent", max_results=3))

    assert results == []


def test_search_does_not_replace_irrelevant_results_with_default_papers():
    service = AcademicSearchService()
    service._search_arxiv = AsyncMock(return_value=[
        {
            "title": "Empirical Evaluation of Transformer Medical Image Segmentation",
            "abstract": "A benchmark of transformer architectures for medical segmentation.",
            "year": 2024,
            "source": "arxiv",
            "relevance_score": 0.95,
        }
    ])
    service._search_semantic_scholar = AsyncMock(return_value=[])
    service._search_openalex = AsyncMock(return_value=[])

    results = asyncio.run(
        service.search(
            "Intelligent Agent",
            max_results=3,
            sources=["arxiv", "semantic_scholar"],
        )
    )

    assert results == []


def test_search_uses_openalex_fallback_when_selected_sources_fail():
    service = AcademicSearchService()
    service._search_arxiv = AsyncMock(
        side_effect=AcademicSearchSourceError("ArXiv returned HTTP 429: Rate exceeded.", status_code=429)
    )
    service._search_semantic_scholar = AsyncMock(
        side_effect=AcademicSearchSourceError("Semantic Scholar returned HTTP 429: Too Many Requests.", status_code=429)
    )
    service._search_openalex = AsyncMock(return_value=[
        {
            "title": "Intelligent Agents for Autonomous Research Planning",
            "abstract": "A framework for intelligent agent decision making and planning.",
            "year": 2024,
            "source": "openalex",
            "relevance_score": 0.85,
        }
    ])

    results = asyncio.run(
        service.search(
            "Intelligent Agent",
            max_results=3,
            sources=["arxiv", "semantic_scholar"],
        )
    )

    assert len(results) == 1
    assert results[0]["source"] == "openalex"


def test_search_uses_openalex_fallback_when_selected_sources_are_irrelevant():
    service = AcademicSearchService()
    service._search_arxiv = AsyncMock(return_value=[
        {
            "title": "Empirical Evaluation of Transformer Medical Image Segmentation",
            "abstract": "A benchmark of transformer architectures for medical segmentation.",
            "year": 2024,
            "source": "arxiv",
            "relevance_score": 0.95,
        }
    ])
    service._search_semantic_scholar = AsyncMock(return_value=[])
    service._search_openalex = AsyncMock(return_value=[
        {
            "title": "Intelligent Agents for Autonomous Research Planning",
            "abstract": "A framework for intelligent agent decision making and planning.",
            "year": 2024,
            "source": "openalex",
            "relevance_score": 0.85,
        }
    ])

    results = asyncio.run(
        service.search(
            "Intelligent Agent",
            max_results=3,
            sources=["arxiv", "semantic_scholar"],
        )
    )

    assert len(results) == 1
    assert results[0]["source"] == "openalex"


def test_search_fetches_larger_candidate_pool_before_ranking(monkeypatch):
    service = AcademicSearchService()
    monkeypatch.setattr(
        "app.services.academic_search.settings.ACADEMIC_SEARCH_CANDIDATE_MULTIPLIER",
        4,
    )
    monkeypatch.setattr(
        "app.services.academic_search.settings.ACADEMIC_SEARCH_MAX_CANDIDATES_PER_SOURCE",
        40,
    )
    monkeypatch.setattr(
        "app.services.academic_search.settings.ACADEMIC_SEARCH_MIN_CANDIDATES_PER_SOURCE",
        30,
    )
    service._search_arxiv = AsyncMock(return_value=[])
    service._search_openalex = AsyncMock(return_value=[])

    asyncio.run(service.search("Intelligent Agent", max_results=5, sources=["arxiv"]))

    service._search_arxiv.assert_awaited_once_with("Intelligent Agent", max_results=30)


def test_search_returns_cached_results_without_calling_sources_again():
    service = AcademicSearchService()
    service._search_arxiv = AsyncMock(return_value=[
        {
            "title": "Intelligent Agents for Autonomous Research Planning",
            "abstract": "A framework for intelligent agent decision making and planning.",
            "year": 2024,
            "source": "arxiv",
            "relevance_score": 0.95,
        }
    ])
    service._search_semantic_scholar = AsyncMock(return_value=[])
    service._search_openalex = AsyncMock(return_value=[])

    first = asyncio.run(
        service.search(
            "Intelligent Agent",
            max_results=3,
            sources=["arxiv", "semantic_scholar"],
        )
    )
    second = asyncio.run(
        service.search(
            "  intelligent   agent  ",
            max_results=3,
            sources=["arxiv", "semantic_scholar"],
        )
    )

    assert first == second
    assert first is not second
    assert service._search_arxiv.call_count == 1
    assert service._search_semantic_scholar.call_count == 1
    assert service._search_openalex.call_count == 0


def test_concurrent_searches_share_inflight_request():
    service = AcademicSearchService()

    async def fake_arxiv_search(query, max_results=10):
        await asyncio.sleep(0.01)
        return [
            {
                "title": "Intelligent Agents for Autonomous Research Planning",
                "abstract": "A framework for intelligent agent decision making and planning.",
                "year": 2024,
                "source": "arxiv",
                "relevance_score": 0.95,
            }
        ]

    service._search_arxiv = AsyncMock(side_effect=fake_arxiv_search)
    service._search_semantic_scholar = AsyncMock(return_value=[])
    service._search_openalex = AsyncMock(return_value=[])

    async def run_searches():
        return await asyncio.gather(
            service.search(
                "Intelligent Agent",
                max_results=3,
                sources=["arxiv", "semantic_scholar"],
            ),
            service.search(
                "  intelligent   agent  ",
                max_results=3,
                sources=["arxiv", "semantic_scholar"],
            ),
        )

    first, second = asyncio.run(run_searches())

    assert first == second
    assert service._search_arxiv.call_count == 1
    assert service._search_semantic_scholar.call_count == 1


def test_search_raises_when_all_sources_fail():
    service = AcademicSearchService()
    service._search_arxiv = AsyncMock(
        side_effect=AcademicSearchSourceError("ArXiv trả HTTP 429: Rate exceeded.", status_code=429)
    )
    service._search_semantic_scholar = AsyncMock(
        side_effect=AcademicSearchSourceError("Semantic Scholar trả HTTP 429: Too Many Requests.", status_code=429)
    )

    service._search_openalex = AsyncMock(
        side_effect=AcademicSearchSourceError("OpenAlex returned HTTP 503: Service unavailable.", status_code=503)
    )

    try:
        asyncio.run(
            service.search(
                "Intelligent Agent",
                max_results=3,
                sources=["arxiv", "semantic_scholar"],
            )
        )
    except AcademicSearchError as exc:
        assert exc.status_code == 429
        assert "ArXiv" in str(exc)
        assert "Semantic Scholar" in str(exc)
    else:
        raise AssertionError("Expected AcademicSearchError when all sources fail")


def test_parse_openalex_abstract_from_inverted_index():
    service = AcademicSearchService()

    abstract = service._parse_openalex_abstract({
        "agents": [2],
        "Intelligent": [0],
        "coordinate": [3],
        "research": [1],
    })

    assert abstract == "Intelligent research agents coordinate"
