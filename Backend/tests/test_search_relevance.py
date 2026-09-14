from app.services.academic_search import AcademicSearchService
from app.services.llm_service import LLMService


def test_mock_keyword_extraction_uses_requested_topic():
    service = LLMService()
    prompt = (
        "Given this research topic or question: 'Intelligent Agent', "
        "extract 3-5 concise academic search keywords (English) for searching academic papers."
    )

    keywords = service._mock_keyword_extraction(prompt)

    assert keywords == "intelligent agent"
    assert "transformer deep learning medical segmentation" not in keywords


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


# @trace: REQ-013
def test_vietnamese_query_keyword_mapping():
    service = LLMService()
    prompt = (
        "Given this research topic or question: 'tác hại của thuốc lá đến cơ thể con người', "
        "extract 3-5 concise academic search keywords (English) for searching academic papers."
    )
    keywords = service._mock_keyword_extraction(prompt)
    assert any(k in keywords.lower() for k in ["tobacco", "smoking", "nicotine"])
    assert "transformer" not in keywords.lower()


# @trace: REQ-013
def test_literature_review_does_not_leak_raw_json():
    service = LLMService()
    writing_prompt = """You are a scientific academic researcher writing a comprehensive Literature Review.
Topic: tác hại của thuốc lá đến cơ thể con người
Requirements:
1. Giới thiệu & Tổng quan bài toán
2. Phân tích Phương pháp & Kiến trúc kỹ thuật
3. Bảng Ma trận So sánh Đối chiếu
4. Thảo luận & Hạn chế Nghiên cứu
5. Hướng phát triển & Khuyến nghị Tương lai
6. Danh mục Tài liệu Tham khảo

Papers analyzed:
Method: Clinical cohort study
"""
    report = service._mock_generation(writing_prompt, None)
    # Ensure it is Markdown with standard headers, NOT raw JSON dictionary
    assert not report.strip().startswith("{")
    assert "## 1. Giới thiệu" in report
    assert "## 2. Phân tích" in report
    assert "tác hại của thuốc lá đến cơ thể con người" in report

