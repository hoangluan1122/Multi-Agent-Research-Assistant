"""
Agent Soạn thảo Báo cáo Nghiên cứu (WritingAgent - UC009, UC011).
Chịu trách nhiệm tổng hợp toàn bộ tri thức (metadata bài báo, kết quả phân tích cấu trúc, bảng so sánh đối chiếu, danh mục trích dẫn)
và sử dụng LLM soạn thảo bài tổng quan Literature Review hoàn chỉnh theo cấu trúc chuẩn mực học thuật.
"""

import logging
import re
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

            # 3.1 Sử dụng Retrieval (RAG) từ Vector Store (Qdrant) theo yêu cầu nhiệm vụ
            retrieval_query = f"{session.topic} {session.research_question or ''}".strip()
            retrieved_chunks = await retrieve_document_chunks(
                session_id=session_id,
                query=retrieval_query,
                top_k=6
            )
            rag_context_lines = []
            for chunk in retrieved_chunks:
                meta = chunk.get("metadata", {})
                title_c = meta.get("paper_title", "Paper")
                page_c = meta.get("page_number", "N/A")
                score_c = chunk.get("score", 0.0)
                txt_c = chunk.get("text", "")[:350]
                rag_context_lines.append(f"- [{title_c} - Trang {page_c} (Điểm {score_c:.2f})]: {txt_c}")
            rag_evidence_text = "\n".join(rag_context_lines) if rag_context_lines else "No specific text chunks retrieved."

            # 4. Tạo prompt chi tiết yêu cầu LLM soạn thảo theo chuẩn mực
            prompt = f"""You are a distinguished scientific academic researcher. Write a comprehensive, rigorous Literature Review report.
Topic: {session.topic}
Research Question: {session.research_question or 'Analyze key state-of-the-art developments, methodologies, and benchmarks.'}

Available Papers & Citations:
{"---".join(papers_context)}

Evidence & Paragraph Chunks from Vector RAG Retrieval:
{rag_evidence_text}

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

            # A report must never fall back to LLMService's generic mock text.  That
            # text is useful for isolated demos, but it makes unrelated research
            # sessions look identical.  If a live model is unavailable, build a
            # complete report from the evidence collected in this session instead.
            evidence_report = self._build_evidence_grounded_report(
                session=session,
                papers=list(papers),
                citations=list(citations),
                citation_map=citation_map,
                comparison_table=comparison_table,
                synthesized_summary=synthesized_summary,
                retrieved_chunks=retrieved_chunks,
                feedback=feedback,
            )
            try:
                generated_content = await llm_service.generate_text(
                    prompt=prompt,
                    system_instruction=(
                        "You are a peer-reviewed academic author. Use only the supplied "
                        "evidence, cite the assigned keys, and do not invent papers, metrics, "
                        "datasets, or results."
                    ),
                    temperature=0.2,
                    allow_mock=False,
                )
            except Exception as llm_error:
                logger.warning("Live LLM generation unavailable; using evidence-grounded report: %s", llm_error)
                generated_content = ""

            content_md = (
                generated_content
                if self._is_source_grounded_report(generated_content, session.topic, list(papers), citation_map)
                else evidence_report
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

    @staticmethod
    def _clean(value: Optional[str], default: str = "Chưa có dữ liệu được trích xuất.") -> str:
        """Make database/LLM fields safe for Markdown without inventing evidence."""
        if not value:
            return default
        return re.sub(r"\s+", " ", str(value)).strip()

    @classmethod
    def _is_source_grounded_report(
        cls,
        content: Optional[str],
        topic: str,
        papers: List[Paper],
        citation_map: Dict[str, Optional[str]],
    ) -> bool:
        """Reject short, generic, or uncited model text before it reaches users."""
        if not content or len(content.strip()) < 1800:
            return False
        normalized = content.casefold()
        if topic and topic.casefold() not in normalized:
            return False
        keys = [key for key in citation_map.values() if key]
        if keys and not any(key in content for key in keys):
            return False
        titles = [p.title.casefold() for p in papers if p.title]
        # At least one real title should be discussed when there are papers.
        return not titles or any(title in normalized for title in titles)

    @classmethod
    def _build_evidence_grounded_report(
        cls,
        session: ResearchSession,
        papers: List[Paper],
        citations: List[Citation],
        citation_map: Dict[str, Optional[str]],
        comparison_table: Optional[str],
        synthesized_summary: Optional[str],
        retrieved_chunks: List[Dict[str, Any]],
        feedback: Optional[str],
    ) -> str:
        """Create a formal, traceable report when a live LLM cannot do so safely.

        Every factual paragraph below is assembled from selected Paper, PaperAnalysis,
        Citation, and RAG records of the current session. Missing fields are disclosed
        instead of replaced by a plausible but unsupported default.
        """
        years = sorted(p.year for p in papers if p.year)
        year_range = f"{years[0]}–{years[-1]}" if years else "không xác định"
        analyzed_count = sum(1 for paper in papers if paper.analysis)
        citation_count = len([c for c in citations if c.citation_key])
        question = cls._clean(
            session.research_question,
            "Chủ đề được tổng hợp theo các tài liệu đã chọn trong phiên nghiên cứu.",
        )

        lines = [
            f"# Báo cáo tổng quan nghiên cứu: {session.topic}",
            "",
            "## Tóm tắt điều hành",
            (
                f"Báo cáo này tổng hợp **{len(papers)}** tài liệu đã được chọn cho chủ đề "
                f"**{session.topic}**. Tập chứng cứ có mốc năm {year_range}; "
                f"{analyzed_count}/{len(papers)} tài liệu có phân tích cấu trúc và "
                f"{citation_count} trích dẫn đã được lập. Nội dung chỉ sử dụng metadata, "
                "phân tích đọc hiểu và các đoạn văn truy hồi của phiên hiện tại; trường dữ liệu "
                "còn thiếu được nêu rõ thay vì suy diễn."
            ),
            "",
            f"**Câu hỏi nghiên cứu.** {question}",
            "",
            "**Từ khóa:** " + ", ".join(filter(None, [session.topic, "tổng quan tài liệu", "phân tích so sánh", "trích dẫn có kiểm chứng"])),
            "",
            "## 1. Phạm vi và phương pháp tổng hợp",
            (
                "Phạm vi của báo cáo là các tài liệu được người dùng chọn trong phiên, không phải "
                "một tổng quan hệ thống đầy đủ trên mọi cơ sở dữ liệu. Mỗi tài liệu được đối chiếu "
                "theo phương pháp, dữ liệu/benchmark, chỉ số, kết quả và hạn chế nếu các trường này "
                "đã được ReadingAgent trích xuất. Các kết luận tổng hợp được giữ ở mức mà tập chứng cứ "
                "hiện có hỗ trợ."
            ),
            "",
            "## 2. Hồ sơ chứng cứ của các tài liệu đã chọn",
        ]

        if not papers:
            lines.extend([
                "",
                "Không có tài liệu được chọn nên chưa thể đưa ra kết luận thực chứng. Hãy chọn hoặc tải lên "
                "ít nhất một paper rồi chạy lại workflow.",
            ])

        for index, paper in enumerate(papers, 1):
            analysis = paper.analysis
            key = citation_map.get(paper.id) or f"[Tài liệu {index}]"
            authors = ", ".join(paper.authors or []) or "Chưa có thông tin tác giả"
            venue = paper.venue or "Chưa có thông tin nơi công bố"
            lines.extend([
                "",
                f"### 2.{index}. {paper.title} {key}",
                f"- **Thông tin thư mục:** {authors} ({paper.year or 'không rõ năm'}), {venue}.",
                f"- **Mục tiêu và bối cảnh:** {cls._clean(paper.abstract, 'Abstract chưa có; phần diễn giải chỉ dựa trên các trường phân tích bên dưới.')}",
                f"- **Phương pháp/kỹ thuật:** {cls._clean(analysis.method if analysis else None)}",
                f"- **Dữ liệu, benchmark và chỉ số:** {cls._clean(analysis.dataset if analysis else None)}; Chỉ số: {cls._clean(analysis.metrics if analysis else None)}",
                f"- **Kết quả hoặc đóng góp được trích xuất:** {cls._clean(analysis.results if analysis else None)}",
                f"- **Giới hạn và điểm cần thận trọng:** {cls._clean(analysis.limitations if analysis else None)}",
            ])
            if analysis and analysis.summary:
                lines.append(f"- **Tóm lược phân tích:** {cls._clean(analysis.summary)}")

        lines.extend(["", "## 3. Tổng hợp và đối chiếu liên tài liệu"])
        if synthesized_summary:
            lines.extend([cls._clean(synthesized_summary), ""])
        else:
            lines.extend([
                (
                    "Các tài liệu trong tập mẫu được đặt cạnh nhau theo các trường đã trích xuất ở phần 2. "
                    "Sự khác biệt về phương pháp, bộ dữ liệu và chỉ số chỉ nên được diễn giải sâu hơn khi các "
                    "trường tương ứng có dữ liệu đầy đủ."
                ),
                "",
            ])
        lines.extend(["### 3.1. Ma trận so sánh", comparison_table or "Chưa tạo được bảng so sánh cho tập tài liệu này."])

        evidence_lines = []
        for chunk in retrieved_chunks[:6]:
            metadata = chunk.get("metadata", {}) or {}
            text = cls._clean(chunk.get("text"), "")
            if text:
                evidence_lines.append(
                    f"- **{metadata.get('paper_title', 'Tài liệu nguồn')}** "
                    f"(trang {metadata.get('page_number', 'không rõ')}): {text[:500]}"
                )
        lines.extend(["", "## 4. Dấu vết chứng cứ từ tài liệu gốc"])
        lines.extend(evidence_lines or ["Không truy hồi được đoạn văn RAG; báo cáo vẫn dựa trên metadata và phân tích cấu trúc ở phần 2."])

        lines.extend([
            "",
            "## 5. Thảo luận, hạn chế và hàm ý",
            (
                "Tập chứng cứ hiện gồm các tài liệu được chọn trong một phiên làm việc; vì vậy mức độ khái quát "
                "phụ thuộc trực tiếp vào độ phủ của nguồn, chất lượng PDF và các trường phân tích đã trích xuất. "
                "Những ô ghi 'Chưa có dữ liệu được trích xuất' cần được bổ sung từ paper gốc trước khi dùng báo cáo "
                "cho quyết định có rủi ro cao hoặc khẳng định định lượng."
            ),
            "",
            "Về thực hành, báo cáo nên được dùng như một bản thảo có truy xuất nguồn: người đọc có thể đối chiếu từng "
            "hồ sơ ở phần 2, ma trận ở phần 3 và đoạn văn gốc ở phần 4 trước khi hoàn thiện kết luận.",
            "",
            "## 6. Hướng phát triển tiếp theo",
            "- Bổ sung tài liệu còn thiếu hoặc mở rộng tiêu chí chọn mẫu để tăng độ phủ của chủ đề.",
            "- Hoàn thiện các trường phương pháp, dữ liệu, chỉ số và hạn chế chưa được trích xuất.",
            "- Rà soát thủ công các trích dẫn trước khi công bố, đặc biệt với tài liệu không có DOI/URL xác thực.",
        ])
        if feedback:
            lines.extend(["", "## 7. Ghi nhận góp ý của vòng phản biện", cls._clean(feedback)])

        lines.extend(["", "## Tài liệu tham khảo"])
        if citations:
            lines.extend(f"{citation.citation_key or '[Ref]'} {citation.citation_text}" for citation in citations)
        else:
            lines.append("Chưa có bản ghi trích dẫn. Cần chạy CitationAgent trước khi xuất bản chính thức.")
        return "\n".join(lines)

# Khởi tạo singleton instance cho WritingAgent
writing_agent = WritingAgent()

