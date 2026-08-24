"""
Tập hợp các Công cụ (Tools) định dạng chuẩn tương thích Google ADK (Agent Development Kit).
Cung cấp chức năng tìm kiếm bài báo, truy xuất đoạn văn bản từ Qdrant (RAG) và định dạng trích dẫn chuẩn học thuật (IEEE/APA).
"""

import logging
from typing import Dict, Any, List, Optional
from app.services.academic_search import academic_search_service
from app.services.qdrant_service import qdrant_service

logger = logging.getLogger("paperflow.adk_tools")

async def search_academic_papers(
    query: str,
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    max_results: int = 5,
    sources: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Công cụ ADK: Tìm kiếm bài báo học thuật từ ArXiv và Semantic Scholar theo câu truy vấn nghiên cứu.
    
    Tham số:
        query: Từ khóa hoặc câu truy vấn học thuật.
        year_start: Năm xuất bản bắt đầu (tùy chọn).
        year_end: Năm xuất bản kết thúc (tùy chọn).
        max_results: Số lượng bài báo tối đa cần thu thập.
        sources: Danh sách các nguồn tìm kiếm (ví dụ: ['arxiv', 'semantic_scholar']).
    
    Trả về:
        Danh sách các dictionary chứa thông tin: tiêu đề, tác giả, tóm tắt, năm, nơi công bố, URL, DOI.
    """
    logger.info(f"[ADK Tool: search_academic_papers] Query: '{query}', max_results={max_results}")
    return await academic_search_service.search(
        query=query,
        year_start=year_start,
        year_end=year_end,
        max_results=max_results,
        sources=sources
    )

async def retrieve_document_chunks(
    session_id: str,
    query: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Công cụ ADK: Truy xuất các đoạn văn bản tương đồng ngữ nghĩa từ Qdrant Vector Store phục vụ RAG.
    
    Tham số:
        session_id: Định danh duy nhất của phiên nghiên cứu.
        query: Câu hỏi hoặc nội dung cần tìm đoạn tài liệu chứng cứ.
        top_k: Số lượng đoạn văn bản liên quan nhất cần trả về.
        
    Trả về:
        Danh sách các đoạn văn bản kèm metadata (số trang, tên mục, điểm tương đồng).
    """
    logger.info(f"[ADK Tool: retrieve_document_chunks] Session: {session_id}, Query: '{query}', top_k={top_k}")
    return await qdrant_service.search_relevant_chunks(
        session_id=session_id,
        query=query,
        top_k=top_k
    )

def format_citation_reference(
    title: str,
    authors: List[str],
    year: Optional[int] = None,
    venue: Optional[str] = None,
    doi: Optional[str] = None,
    url: Optional[str] = None,
    style: str = "IEEE"
) -> str:
    """
    Công cụ ADK: Định dạng một mục tài liệu tham khảo theo quy chuẩn học thuật IEEE hoặc APA.
    
    Tham số:
        title: Tiêu đề bài báo.
        authors: Danh sách tên các tác giả.
        year: Năm xuất bản.
        venue: Tạp chí hoặc hội nghị công bố.
        doi: Mã định danh số đối tượng (DOI).
        url: Đường dẫn liên kết trực tuyến.
        style: Chuẩn trích dẫn ("IEEE" hoặc "APA").
        
    Trả về:
        Chuỗi trích dẫn tài liệu tham khảo đã được định dạng chuẩn.
    """
    authors_str = ", ".join(authors[:3]) if authors else "Anonymous"
    if authors and len(authors) > 3:
        authors_str += " et al."

    year_str = str(year) if year else "n.d."
    venue_str = venue if venue else "Academic Repository"
    doi_str = f" DOI: {doi}" if doi else (f" Available: {url}" if url else "")

    if style.upper() == "APA":
        return f"{authors_str} ({year_str}). {title}. *{venue_str}*.{doi_str}"
    else:
        # Mặc định theo chuẩn IEEE
        return f'{authors_str}, "{title}," in *{venue_str}*, {year_str}.{doi_str}'

