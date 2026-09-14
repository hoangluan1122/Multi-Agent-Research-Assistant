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
    assert "## 1. Giới thiệu" in report
    assert "## 2. Phân tích" in report
    assert "tác hại của thuốc lá đến cơ thể con người" in report


# @trace: REQ-014, REQ-015
def test_fallback_papers_generates_exact_count_and_safe_urls():
    service = AcademicSearchService()
    count_5 = service._generate_fallback_papers("smartphone screen time", count=5)
    assert len(count_5) == 5, f"Expected 5 papers, got {len(count_5)}"
    
    count_8 = service._generate_fallback_papers("smartphone screen time", count=8)
    assert len(count_8) == 8, f"Expected 8 papers, got {len(count_8)}"

    # Ensure URLs are valid search URLs and DO NOT link to the unrelated finance paper 2401.00001
    for p in count_5:
        assert "2401.00001" not in p["url"]
        assert "scholar.google.com" in p["url"] or "arxiv.org/search" in p["url"]
        assert "smartphone" in p["url"] or "screen" in p["url"]


# @trace: REQ-016
def test_smartphone_vietnamese_query_mapping():
    service = LLMService()
    prompt = (
        "Given this research topic or question: 'tác hại điện thoại', "
        "extract 3-5 concise academic search keywords (English) for searching academic papers."
    )
    keywords = service._mock_keyword_extraction(prompt)
    assert any(k in keywords.lower() for k in ["smartphone", "screen", "mobile", "phone"])
    assert "transformer" not in keywords.lower()


# @trace: REQ-017
def test_money_vietnamese_query_mapping():
    service = LLMService()
    prompt = (
        "Given this research topic or question: 'tiền', "
        "extract 3-5 concise academic search keywords (English) for searching academic papers."
    )
    keywords = service._mock_keyword_extraction(prompt)
    assert any(k in keywords.lower() for k in ["money", "currency", "monetary", "finance", "banking"])
    assert "prostate" not in keywords.lower()


# @trace: REQ-017, REQ-018
def test_money_query_filters_prostate_papers():
    service = AcademicSearchService()
    papers = [
        {
            "title": "Phí bảo hiểm tiền gửi và hạn mức trả tiền bảo hiểm tại Việt Nam",
            "abstract": "Nghiên cứu về cơ chế bảo hiểm tiền gửi và an toàn hệ thống ngân hàng.",
            "year": 2024,
            "url": "https://doi.org/10.1234/finance.001"
        },
        {
            "title": "ĐẶC ĐIỂM VÀ SO SÁNH GIÁ TRỊ CỦA KHÁNG NGUYÊN ĐẶC HIỆU TUYẾN TIỀN LIỆT TOÀN PHẦN (PSAT)",
            "abstract": "Nghiên cứu lâm sàng về sinh hóa tuyến tiền liệt trong chẩn đoán ung thư.",
            "year": 2023,
            "url": "https://doi.org/10.1234/med.002"
        },
        {
            "title": "DÒNG TIỀN, CHẤT LƯỢNG LỢI NHUẬN VÀ NẮM GIỮ TIỀN MẶT TẠI VIỆT NAM",
            "abstract": "Phân tích tài chính doanh nghiệp và lượng tiền mặt.",
            "year": 2024,
            "url": "https://doi.org/10.31219/osf.io/paxh6"
        }
    ]

    ranked = service._rank_by_query_match("tiền", papers)
    titles = [p["title"] for p in ranked]
    # Ensure prostate paper is rejected
    assert not any("TUYẾN TIỀN LIỆT" in t for t in titles)
    assert any("tiền gửi" in t for t in titles)



