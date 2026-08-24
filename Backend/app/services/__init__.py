"""
Package chứa các Service phụ trợ (Core Business Services) của PaperFlow:
- LLMService: Tương tác với các mô hình ngôn ngữ lớn (Gemini, OpenAI, Mock).
- QdrantService: Quản lý Vector DB, tính embedding và tìm kiếm ngữ nghĩa RAG.
- PDFParser: Đọc, chuẩn hóa và chia nhỏ tài liệu PDF thành các chunks.
- AcademicSearchService: Tìm kiếm bài báo học thuật từ arXiv và Semantic Scholar.
- ExportService: Xuất báo cáo nghiên cứu sang định dạng Markdown, Word (.docx), PDF.
"""

from app.services.llm_service import llm_service, LLMService
from app.services.qdrant_service import qdrant_service, QdrantService
from app.services.pdf_parser import pdf_parser, PDFParser
from app.services.academic_search import academic_search_service, AcademicSearchService
from app.services.export_service import export_service, ExportService

__all__ = [
    "llm_service",
    "LLMService",
    "qdrant_service",
    "QdrantService",
    "pdf_parser",
    "PDFParser",
    "academic_search_service",
    "AcademicSearchService",
    "export_service",
    "ExportService",
]

