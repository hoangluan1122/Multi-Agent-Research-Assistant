"""
Agent Tóm tắt và So sánh đối chiếu (SummarizationAgent - UC006, UC007).
Chịu trách nhiệm tổng hợp các phát hiện then chốt từ các bài báo đã phân tích, xây dựng bảng ma trận so sánh (Markdown table) và phân tích bức tranh toàn cảnh.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from .base import BaseAgent
from .adk_tools import retrieve_document_chunks
from ..models.paper import Paper
from ..services.llm_service import llm_service

logger = logging.getLogger("paperflow.summarization_agent")

class SummarizationAgent(BaseAgent):
    MISSING_DATA = "Chưa trích xuất được dữ liệu."
    """
    SummarizationAgent: Tác tử tổng hợp và so sánh:
    - Thu thập toàn bộ kết quả phân tích (PaperAnalysis) của phiên nghiên cứu.
    - Xây dựng ma trận so sánh đa chiều (Phương pháp, Bộ dữ liệu, Kết quả, Hạn chế).
    - Sử dụng LLM viết phần tổng hợp so sánh mạch lạc (Synthesized Comparative Narrative).
    """
    def __init__(self):
        super().__init__(
            name="SummarizationAgent",
            description="Tóm tắt nghiên cứu và xây dựng ma trận/bảng so sánh đối chiếu giữa các bài báo (UC006, UC007).",
            instruction="""Bạn là chuyên gia tổng hợp và đối chiếu nghiên cứu khoa học.
            Nhiệm vụ: Tổng hợp các phát hiện then chốt, xây dựng ma trận so sánh chi tiết giữa các bài báo
            (Phương pháp, Tập dữ liệu, Kết quả & Chỉ số, Hạn chế) và phân tích bức tranh tổng thể.""",
            tools=[retrieve_document_chunks]
        )

    async def run(
        self,
        db: AsyncSession,
        session_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Thực thi quy trình tóm tắt và xây dựng ma trận đối chiếu:
        1. Lấy danh sách các bài báo kèm kết quả phân tích trong phiên.
        2. Dựng bảng ma trận so sánh bằng Markdown.
        3. Dùng LLM tổng hợp bức tranh toàn cảnh về điểm mạnh, sự đánh đổi và thách thức mở.
        """
        run = await self.log_start(
            db,
            session_id,
            step_description="Tổng hợp tóm tắt và xây dựng bảng so sánh nghiên cứu theo chuẩn ADK"
        )

        try:
            # 1. Truy vấn các bài báo được chọn và kết quả phân tích
            stmt = (
                select(Paper)
                .where(Paper.session_id == session_id, Paper.is_selected.is_(True))
                .options(selectinload(Paper.analysis))
            )
            res = await db.execute(stmt)
            papers = res.scalars().all()

            if not papers:
                await self.log_end(db, run, status="COMPLETED", output_data={"comparison_table": ""})
                return {"comparison_table": "", "synthesized_summary": ""}

            # 2. Xây dựng bảng ma trận so sánh Markdown
            comparison_table_md = self._generate_markdown_table(list(papers))

            # 3. Sử dụng LLM tổng hợp phân tích đối chiếu chuyên sâu
            paper_details_text = []
            for idx, p in enumerate(papers, 1):
                analysis = p.analysis
                paper_details_text.append(
                    f"[{idx}] Title: {p.title} ({p.year})\n"
                    f"Method: {analysis.method if analysis else 'N/A'}\n"
                    f"Dataset: {analysis.dataset if analysis else 'N/A'}\n"
                    f"Results: {analysis.results if analysis else 'N/A'}\n"
                    f"Limitations: {analysis.limitations if analysis else 'N/A'}\n"
                )

            prompt = f"""You are a senior scientific research reviewer. Synthesize and compare the following {len(papers)} research papers.
Identify common architectural themes, comparative strengths, trade-offs, and open challenges.

Paper Analyses:
{"---".join(paper_details_text)}

Provide a coherent comparative synthesis (2-3 paragraphs in Vietnamese or English based on research domain).
"""
            # A generic offline fallback can describe an unrelated domain and make
            # the final report look fabricated.  Keep this synthesis grounded in
            # the papers from the current session when the configured model is
            # unavailable.
            try:
                synthesized_text = await llm_service.generate_text(
                    prompt,
                    temperature=0.2,
                    allow_mock=False,
                )
            except Exception as exc:
                logger.warning("Comparative LLM synthesis unavailable; using source-only summary: %s", exc)
                synthesized_text = self._build_source_only_summary(list(papers))

            output = {
                "comparison_table": comparison_table_md,
                "synthesized_summary": synthesized_text,
                "total_papers_compared": len(papers)
            }

            await self.log_end(db, run, status="COMPLETED", output_data=output)
            return output

        except Exception as e:
            logger.error(f"[{self.name}] Error: {e}", exc_info=True)
            await self.log_end(db, run, status="FAILED", error_message=str(e))
            raise

    def _generate_markdown_table(self, papers: List[Paper]) -> str:
        """Tạo bảng Markdown chuẩn hóa so sánh đa chiều giữa các bài báo khoa học."""
        headers = ["No.", "Paper Title & Year", "Method / Architecture", "Dataset / Benchmarks", "Key Results & Metrics", "Limitations"]
        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |"
        ]

        for idx, p in enumerate(papers, 1):
            ana = p.analysis
            method = self._table_value(ana.method if ana else None)
            dataset = self._table_value(ana.dataset if ana else None)
            results = self._table_value(ana.results if ana else None)
            limits = self._table_value(ana.limitations if ana else None)
            
            row = [
                str(idx),
                f"**{self._table_value(p.title)}** ({p.year or 'N/A'})",
                method,
                dataset,
                results,
                limits,
            ]
            lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)

    @classmethod
    def _build_source_only_summary(cls, papers: List[Paper]) -> str:
        """Create a transparent summary from stored metadata, never a mock claim."""
        available = [p for p in papers if p.analysis and any(
            cls._table_value(getattr(p.analysis, field)) != cls.MISSING_DATA
            for field in ("method", "dataset", "results", "limitations")
        )]
        if not available:
            return (
                "Chưa thể tổng hợp so sánh chuyên sâu vì mô hình AI chưa trích xuất "
                "được Method, Dataset, Results và Limitations từ các tài liệu nguồn. "
                "Danh sách bài và metadata vẫn được giữ nguyên để chạy lại sau khi cấu hình LLM hợp lệ."
            )

        lines = [
            f"Tổng hợp được xây dựng từ dữ liệu đã trích xuất của {len(available)}/{len(papers)} bài báo."
        ]
        for paper in available:
            summary = (paper.analysis.summary or paper.abstract or "").strip()
            if summary:
                lines.append(f"- **{paper.title}**: {summary[:500]}")
        return "\n".join(lines)

    @classmethod
    def _table_value(cls, value: Optional[str]) -> str:
        """Display missing extraction transparently instead of a generic research claim."""
        if not value or not value.strip():
            return cls.MISSING_DATA
        return value.replace("\n", " ").replace("|", "\\|").strip()

# Khởi tạo singleton instance cho SummarizationAgent
summarization_agent = SummarizationAgent()

