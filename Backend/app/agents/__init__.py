"""
Package chứa các Agent chuyên trách trong hệ sinh thái Multi-Agent của PaperFlow:
- BaseAgent: Lớp cơ sở trừu tượng tích hợp Google ADK và cơ chế ghi log lịch sử thực thi.
- SearchAgent (UC002): Tìm kiếm, lọc và xếp hạng tài liệu học thuật.
- ReadingAgent (UC004, UC005): Đọc PDF, trích xuất cấu trúc và đánh chỉ mục vector RAG vào Qdrant.
- SummarizationAgent (UC006, UC007): Tóm tắt và xây dựng ma trận so sánh các phương pháp.
- CitationAgent (UC008): Quản lý, chuẩn hóa định dạng trích dẫn (IEEE, APA) và xác thực DOI.
- WritingAgent (UC009, UC011): Soạn thảo bài tổng quan Literature Review hoàn chỉnh.
- ReviewAgent (UC010): Phản biện, thẩm định rủi ro ảo giác và chấm điểm chất lượng báo cáo.
- adk_tools: Bộ công cụ chuẩn hóa tương thích Google ADK Tool.
"""

from .base import BaseAgent
from .search_agent import search_agent, SearchAgent
from .reading_agent import reading_agent, ReadingAgent
from .summarization_agent import summarization_agent, SummarizationAgent
from .citation_agent import citation_agent, CitationAgent
from .writing_agent import writing_agent, WritingAgent
from .review_agent import review_agent, ReviewAgent
from . import adk_tools

__all__ = [
    "BaseAgent",
    "search_agent",
    "SearchAgent",
    "reading_agent",
    "ReadingAgent",
    "summarization_agent",
    "SummarizationAgent",
    "citation_agent",
    "CitationAgent",
    "writing_agent",
    "WritingAgent",
    "review_agent",
    "ReviewAgent",
    "adk_tools",
]

