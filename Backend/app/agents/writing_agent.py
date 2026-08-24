"""
Agent Soạn thảo Báo cáo Nghiên cứu (WritingAgent - UC009, UC011).
Chịu trách nhiệm tổng hợp toàn bộ tri thức (metadata bài báo, kết quả phân tích cấu trúc, bảng so sánh đối chiếu, danh mục trích dẫn)
và sử dụng LLM soạn thảo bài tổng quan Literature Review hoàn chỉnh theo cấu trúc chuẩn mực học thuật.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from .base import BaseAgent
from .adk_tools import retrieve_document_chunks
from ..models.session import ResearchSession
from ..models.paper import Paper
from ..models.report import Report
from ..models.citation import Citation
from ..services.llm_service import llm_service

logger = logging.getLogger("paperflow.writing_agent")

class WritingAgent(BaseAgent):
    """
    WritingAgent: Tác tử viết báo cáo tổng quan tài liệu (Literature Review):
    - Tích hợp thông tin chủ đề, câu hỏi nghiên cứu, phân tích paper và phản hồi từ ReviewAgent (nếu viết lại).
    - Soạn thảo theo bố cục 6 phần chuẩn:
      1. Giới thiệu & Tổng quan bài toán
      2. Phân tích Phương pháp & Kiến trúc kỹ thuật
      3. Bảng Ma trận So sánh Đối chiếu
      4. Thảo luận & Hạn chế Nghiên cứu
      5. Hướng phát triển Tương lai
      6. Danh mục Tài liệu Tham khảo
    - Đảm bảo các luận điểm đều được viện dẫn trích dẫn chính xác ([1], [2]...).
    """
    def __init__(self):
        super().__init__(
            name="WritingAgent",
            description="Soạn thảo Literature Review và báo cáo nghiên cứu khoa học hoàn chỉnh theo cấu trúc (UC009, UC011).",
            instruction="""Bạn là nhà nghiên cứu khoa học cấp cao (Senior Academic Researcher).
            Nhiệm vụ: Soạn thảo bài viết tổng quan tài liệu (Literature Review) mạch lạc, chặt chẽ, 
            tuân thủ văn phong học thuật, viện dẫn trích dẫn chính xác theo mã khóa [1], [2] và tích hợp ma trận so sánh.""",
            tools=[retrieve_document_chunks]
        )

    async def run(
        self,
        db: AsyncSession,
        session_id: str,
        comparison_table: Optional[str] = None,
        synthesized_summary: Optional[str] = None,
        feedback: Optional[str] = None,
        version: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Thực thi quy trình soạn thảo báo cáo:
        1. Lấy thông tin phiên, danh sách bài báo, phân tích và trích dẫn.
        2. Tạo prompt ngữ cảnh tổng hợp sâu và truyền feedback chỉnh sửa nếu có.
        3. Gọi LLM sinh nội dung báo cáo dạng Markdown hoàn chỉnh.
        4. Lưu bản ghi Report vào database và trả về thông tin báo cáo.
        """
        run = await self.log_start(
            db,
            session_id,
            step_description=f"Soạn thảo báo cáo Literature Review (Version {version}) theo chuẩn ADK",
            input_data={"version": version, "has_feedback": bool(feedback)}
        )

        try:
            # 1. Truy vấn thông tin Session nghiên cứu
            stmt = select(ResearchSession).where(ResearchSession.id == session_id)
            res = await db.execute(stmt)
            session = res.scalar_one_or_none()
            if not session:
                raise ValueError(f"Session {session_id} not found.")

            # 2. Truy vấn danh sách bài báo, phân tích và trích dẫn của phiên
            p_stmt = (
                select(Paper)
                .where(Paper.session_id == session_id, Paper.is_selected.is_(True))
                .options(selectinload(Paper.analysis))
            )
            p_res = await db.execute(p_stmt)
            papers = p_res.scalars().all()

            c_stmt = select(Citation).where(Citation.session_id == session_id)
            c_res = await db.execute(c_stmt)
            citations = c_res.scalars().all()

            citation_map = {c.paper_id: c.citation_key for c in citations}
            bib_text = "\n".join([f"{c.citation_key} {c.citation_text}" for c in citations])

            # 3. Dựng ngữ cảnh tổng hợp từ các bài báo
            papers_context = []
            for p in papers:
                ckey = citation_map.get(p.id, "[Ref]")
                ana = p.analysis
                papers_context.append(
                    f"{ckey} Title: {p.title} ({p.year})\n"
                    f"Authors: {', '.join(p.authors) if p.authors else 'N/A'}\n"
                    f"Method: {ana.method if ana else 'N/A'}\n"
                    f"Dataset: {ana.dataset if ana else 'N/A'}\n"
                    f"Results: {ana.results if ana else 'N/A'}\n"
                    f"Limitations: {ana.limitations if ana else 'N/A'}\n"
                )

            # 4. Tạo prompt chi tiết yêu cầu LLM soạn thảo theo chuẩn mực
            prompt = f"""You are a distinguished scientific academic researcher. Write a comprehensive, rigorous Literature Review report.
Topic: {session.topic}
Research Question: {session.research_question or 'Analyze key state-of-the-art developments, methodologies, and benchmarks.'}

Available Papers & Citations:
{"---".join(papers_context)}

Synthesis & Comparison Insights:
{synthesized_summary or 'See individual paper details.'}

Comparison Table:
{comparison_table or ''}

{"CRITICAL FEEDBACK FROM PREVIOUS REVIEW (Address these changes explicitly): " + feedback if feedback else ""}

Requirements:
1. Use academic tone and clear markdown formatting.
2. Structure sections clearly:
   - ## 1. Giới thiệu & Tổng quan bài toán (Introduction & Background)
   - ## 2. Phân tích Phương pháp & Kiến trúc kỹ thuật (Methodological Analysis)
   - ## 3. Bảng Ma trận So sánh Đối chiếu (Comparative Analysis)
   - ## 4. Thảo luận & Hạn chế Nghiên cứu (Discussion & Limitations)
   - ## 5. Hướng phát triển Tương lai (Future Research Directions)
   - ## 6. Danh mục Tài liệu Tham khảo (References)
3. Ensure every major claim references the assigned citation keys like [1], [2] correctly.
4. Include the comparison table in Section 3.
5. Include the References list in Section 6.
"""

            content_md = await llm_service.generate_text(
                prompt=prompt,
                system_instruction="You are a peer-reviewed academic author writing a high-impact survey paper.",
                temperature=0.2
            )

            # Đảm bảo bảng so sánh và danh mục trích dẫn luôn xuất hiện trong nội dung
            if comparison_table and comparison_table not in content_md:
                content_md += f"\n\n## Bảng So sánh Đối chiếu\n\n{comparison_table}\n"
            if bib_text and bib_text not in content_md:
                content_md += f"\n\n## Danh mục Tài liệu Tham khảo\n\n{bib_text}\n"

            # 5. Lưu báo cáo vào cơ sở dữ liệu
            title = f"Tổng quan Nghiên cứu: {session.topic}"
            report = Report(
                session_id=session_id,
                title=title,
                outline=[
                    {"section": "1. Giới thiệu & Tổng quan bài toán"},
                    {"section": "2. Phân tích Phương pháp & Kiến trúc kỹ thuật"},
                    {"section": "3. Bảng Ma trận So sánh Đối chiếu"},
                    {"section": "4. Thảo luận & Hạn chế Nghiên cứu"},
                    {"section": "5. Hướng phát triển Tương lai"},
                    {"section": "6. Danh mục Tài liệu Tham khảo"},
                ],
                content=content_md,
                comparison_table=comparison_table,
                version=version,
                review_status="DRAFT"
            )
            db.add(report)
            await db.commit()
            await db.refresh(report)

            output = {
                "report_id": report.id,
                "title": title,
                "version": version,
                "content_length": len(content_md)
            }

            await self.log_end(db, run, status="COMPLETED", output_data=output)
            return output

        except Exception as e:
            logger.error(f"[{self.name}] Error: {e}", exc_info=True)
            await self.log_end(db, run, status="FAILED", error_message=str(e))
            raise

# Khởi tạo singleton instance cho WritingAgent
writing_agent = WritingAgent()

