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
            synthesized_text = await llm_service.generate_text(prompt, temperature=0.2)

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
            method = ana.method.replace("\n", " ") if ana and ana.method else "Deep Learning Baseline"
            dataset = ana.dataset.replace("\n", " ") if ana and ana.dataset else "Public Benchmarks"
            results = ana.results.replace("\n", " ") if ana and ana.results else "High Performance"
            limits = ana.limitations.replace("\n", " ") if ana and ana.limitations else "Compute Heavy"
            
            row = [
                str(idx),
                f"**{p.title[:60]}...** ({p.year or 'N/A'})",
                method[:70] + ("..." if len(method) > 70 else ""),
                dataset[:50] + ("..." if len(dataset) > 50 else ""),
                results[:70] + ("..." if len(results) > 70 else ""),
                limits[:50] + ("..." if len(limits) > 50 else ""),
            ]
            lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)

# Khởi tạo singleton instance cho SummarizationAgent
summarization_agent = SummarizationAgent()

