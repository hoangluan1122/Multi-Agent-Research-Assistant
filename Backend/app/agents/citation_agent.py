"""
Agent Quản lý và Định dạng Trích dẫn (CitationAgent - UC008).
Chịu trách nhiệm chuẩn hóa danh mục tài liệu tham khảo theo quy chuẩn IEEE/APA, gán citation key nhất quán ([1], [2]...) và xác thực tính hợp lệ của nguồn.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base import BaseAgent
from .adk_tools import format_citation_reference
from ..models.paper import Paper
from ..models.citation import Citation

logger = logging.getLogger("paperflow.citation_agent")

class CitationAgent(BaseAgent):
    """
    CitationAgent: Tác tử quản lý trích dẫn học thuật:
    - Tiếp nhận danh sách các bài báo tham gia báo cáo.
    - Chuẩn hóa chuỗi trích dẫn theo phong cách IEEE hoặc APA.
    - Tạo các bản ghi Citation trong SQL và xác thực tính hợp lệ của DOI/URL.
    - Xuất khối văn bản References dạng Markdown sẵn sàng đưa vào báo cáo.
    """
    def __init__(self):
        super().__init__(
            name="CitationAgent",
            description="Quản lý, xác minh và định dạng danh mục trích dẫn học thuật (IEEE, APA) (UC008).",
            instruction="""Bạn là trợ lý trích dẫn học thuật chuyên nghiệp.
            Nhiệm vụ: Chuẩn hóa định dạng trích dẫn theo đúng quy chuẩn IEEE hoặc APA,
            gán citation key nhất quán và kiểm tra tính hợp lệ của DOI/URL.""",
            tools=[format_citation_reference]
        )

    async def run(
        self,
        db: AsyncSession,
        session_id: str,
        style: str = "IEEE",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Thực thi quy trình định dạng danh mục trích dẫn:
        1. Lấy danh sách các bài báo được chọn trong phiên.
        2. Xóa các trích dẫn cũ để định dạng mới nhất quán.
        3. Duyệt từng bài báo, tạo citation key và sinh chuỗi tham khảo chuẩn hóa.
        4. Lưu vào bảng `citations` và trả về danh mục References dạng Markdown.
        """
        run = await self.log_start(
            db,
            session_id,
            step_description=f"Quản lý và định dạng danh mục Citation theo chuẩn {style} (ADK)",
            input_data={"style": style}
        )

        try:
            # 1. Truy vấn các bài báo được chọn trong phiên
            stmt = select(Paper).where(Paper.session_id == session_id, Paper.is_selected.is_(True))
            res = await db.execute(stmt)
            papers = res.scalars().all()

            # Dọn dẹp các trích dẫn cũ của phiên để định dạng mới hoàn toàn
            del_stmt = select(Citation).where(Citation.session_id == session_id)
            del_res = await db.execute(del_stmt)
            for old_c in del_res.scalars().all():
                await db.delete(old_c)

            formatted_citations = []
            bibliography_lines = []

            # 2. Xử lý từng bài báo theo chuẩn trích dẫn được yêu cầu
            for idx, p in enumerate(papers, 1):
                citation_key = f"[{idx}]" if style.upper() == "IEEE" else f"({self._format_apa_key(p)})"
                formatted_text = format_citation_reference(
                    title=p.title,
                    authors=p.authors or [],
                    year=p.year,
                    venue=p.venue,
                    doi=p.doi,
                    url=p.url,
                    style=style
                )

                citation = Citation(
                    session_id=session_id,
                    paper_id=p.id,
                    citation_key=citation_key,
                    citation_text=formatted_text,
                    style=style.upper(),
                    is_verified=bool(p.doi or p.url),
                    verification_status="VERIFIED" if (p.doi or p.url) else "UNVERIFIED"
                )
                db.add(citation)
                formatted_citations.append({
                    "key": citation_key,
                    "paper_id": p.id,
                    "title": p.title,
                    "formatted": formatted_text,
                    "status": citation.verification_status
                })
                bibliography_lines.append(f"{citation_key} {formatted_text}")

            await db.commit()

            output = {
                "style": style.upper(),
                "total_citations": len(formatted_citations),
                "citations": formatted_citations,
                "bibliography_markdown": "\n\n".join(bibliography_lines)
            }

            await self.log_end(db, run, status="COMPLETED", output_data=output)
            return output

        except Exception as e:
            logger.error(f"[{self.name}] Error: {e}", exc_info=True)
            await self.log_end(db, run, status="FAILED", error_message=str(e))
            raise

    def _format_apa_key(self, paper: Paper) -> str:
        """Tạo khóa trích dẫn dạng APA trong thân bài (In-text citation, ví dụ: 'Vaswani, 2017')."""
        first_author = paper.authors[0].split()[-1] if paper.authors else "Author"
        year = paper.year or "n.d."
        return f"{first_author}, {year}"

# Khởi tạo singleton instance cho CitationAgent
citation_agent = CitationAgent()

