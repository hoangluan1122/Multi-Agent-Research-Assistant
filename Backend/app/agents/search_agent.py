"""
Agent Tìm kiếm tài liệu học thuật (SearchAgent - UC002).
Chịu trách nhiệm tối ưu hóa từ khóa học thuật tiếng Anh qua LLM, gọi ADK Search Tool từ ArXiv/Semantic Scholar và lưu trữ danh sách bài báo vào cơ sở dữ liệu.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base import BaseAgent
from .adk_tools import search_academic_papers
from ..models.paper import Paper
from ..models.session import ResearchSession
from ..services.llm_service import llm_service

logger = logging.getLogger("paperflow.search_agent")

class SearchAgent(BaseAgent):
    """
    SearchAgent: Kế thừa BaseAgent, tích hợp công cụ search_academic_papers:
    - Tiếp nhận chủ đề/câu hỏi nghiên cứu.
    - Dùng LLM tối ưu câu truy vấn thành các thuật ngữ chuyên ngành tiếng Anh chuẩn.
    - Tìm kiếm từ các nguồn ArXiv, Semantic Scholar.
    - Lưu metadata các bài báo vào bảng `papers`.
    """
    def __init__(self):
        super().__init__(
            name="SearchAgent",
            description="Tìm kiếm, lọc và xếp hạng các tài liệu học thuật theo chủ đề nghiên cứu (UC002).",
            instruction="""Bạn là trợ lý nghiên cứu khoa học chuyên sâu phụ trách tìm kiếm tài liệu.
            Nhiệm vụ: Phân tích chủ đề nghiên cứu, tối ưu hóa các từ khóa học thuật tiếng Anh,
            truy vấn bài báo từ các kho lưu trữ (ArXiv, Semantic Scholar) và xếp hạng mức độ liên quan.""",
            tools=[search_academic_papers]
        )

    async def run(
        self,
        db: AsyncSession,
        session_id: str,
        query: Optional[str] = None,
        year_start: Optional[int] = None,
        year_end: Optional[int] = None,
        max_papers: int = 10,
        sources: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Thực thi quy trình tìm kiếm tài liệu:
        1. Lấy thông tin phiên nghiên cứu nếu chưa truyền trực tiếp query.
        2. Tối ưu hóa từ khóa tìm kiếm tiếng Anh qua LLM.
        3. Gọi công cụ tìm kiếm học thuật `search_academic_papers`.
        4. Lưu thông tin các bài báo vào cơ sở dữ liệu và ghi log hoàn tất.
        """
        run = await self.log_start(
            db,
            session_id,
            step_description=f"Tìm kiếm tài liệu học thuật cho truy vấn: {query or 'Session Topic'}",
            input_data={"query": query, "max_papers": max_papers, "sources": sources}
        )

        try:
            # 1. Truy vấn thông tin Session nếu query không được truyền trực tiếp
            if not query:
                stmt = select(ResearchSession).where(ResearchSession.id == session_id)
                res = await db.execute(stmt)
                session = res.scalar_one_or_none()
                if not session:
                    raise ValueError(f"Session {session_id} not found.")
                query = session.topic
                params = session.parameters or {}
                year_start = year_start or params.get("year_start")
                year_end = year_end or params.get("year_end")
                max_papers = max_papers or params.get("max_papers", 10)

            # 2. Tối ưu hóa từ khóa tìm kiếm học thuật bằng LLM
            refined_query = await self._optimize_search_query(query)
            logger.info(f"[{self.name}] Optimized query: '{refined_query}'")

            # 3. Gọi công cụ tìm kiếm học thuật ADK Tool
            raw_papers = await search_academic_papers(
                query=refined_query,
                year_start=year_start,
                year_end=year_end,
                max_results=max_papers,
                sources=sources
            )

            # 4. Lưu danh sách bài báo vào Database (Tự động dịch sang Tiếng Việt)
            saved_papers = []
            for item in raw_papers:
                raw_title = item["title"]
                raw_abstract = item.get("abstract", "")
                
                # Tự động chuyển ngữ tiêu đề và tóm tắt sang Tiếng Việt
                trans_prompt = f"""Translate this academic paper title and abstract into Vietnamese (Tiếng Việt):
Title: {raw_title}
Abstract: {raw_abstract}
Respond in JSON:
{{"title_vi": "...", "abstract_vi": "..."}}"""
                try:
                    trans_res = await llm_service.generate_json(trans_prompt)
                    final_title = trans_res.get("title_vi") or raw_title
                    final_abstract = trans_res.get("abstract_vi") or raw_abstract
                except Exception:
                    final_title = raw_title
                    final_abstract = raw_abstract

                paper = Paper(
                    session_id=session_id,
                    title=final_title,
                    authors=item.get("authors", []),
                    abstract=final_abstract,
                    year=item.get("year"),
                    venue=item.get("venue"),
                    doi=item.get("doi"),
                    url=item.get("url"),
                    pdf_path=item.get("pdf_path"),
                    source=item.get("source", "arxiv"),
                    relevance_score=item.get("relevance_score", 0.9),
                    is_selected=True,
                    ingestion_status="PENDING"
                )
                db.add(paper)
                saved_papers.append(paper)

            await db.commit()

            output = {
                "total_found": len(saved_papers),
                "papers": [
                    {
                        "id": p.id,
                        "title": p.title,
                        "year": p.year,
                        "authors": p.authors,
                        "source": p.source
                    }
                    for p in saved_papers
                ]
            }

            await self.log_end(db, run, status="COMPLETED", output_data=output)
            return output

        except Exception as e:
            logger.error(f"[{self.name}] Error: {e}", exc_info=True)
            await self.log_end(db, run, status="FAILED", error_message=str(e))
            raise

    async def _optimize_search_query(self, topic: str) -> str:
        """Sử dụng LLM trích xuất 3-5 từ khóa học thuật tiếng Anh cô đọng nhất từ chủ đề người dùng nhập."""
        prompt = f"Given this research topic or question: '{topic}', extract 3-5 concise academic search keywords (English) for searching academic papers. Return ONLY the search terms separated by space."
        result = await llm_service.generate_text(prompt, temperature=0.1)
        cleaned = result.strip().replace('"', '').replace('\n', ' ')
        return cleaned if cleaned else topic

# Khởi tạo singleton instance cho SearchAgent
search_agent = SearchAgent()

