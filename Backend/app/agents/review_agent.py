"""
Agent Thẩm định và Phản biện Học thuật (ReviewAgent - UC010).
Chịu trách nhiệm đánh giá chất lượng bản thảo Literature Review theo 3 tiêu chí:
1. Tính chặt chẽ học thuật & tính hoàn thiện của cấu trúc.
2. Độ bao phủ và tính chính xác của trích dẫn (phát hiện trích dẫn giả mạo).
3. Phát hiện rủi ro ảo giác (Hallucination Detection) và chấm điểm thang 0-100 (PASS/FAIL).
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from .base import BaseAgent
from .adk_tools import retrieve_document_chunks
from ..models.report import Report, Review
from ..models.citation import Citation
from ..services.llm_service import llm_service

logger = logging.getLogger("paperflow.review_agent")

class ReviewAgent(BaseAgent):
    """
    ReviewAgent: Tác tử thẩm định chất lượng học thuật:
    - Kiểm tra tỷ lệ trích dẫn thực tế so với danh mục bài báo đã đọc.
    - Dùng LLM đánh giá logic, phát hiện các luận điểm bị ảo giác (hallucination).
    - Chấm điểm số (0 - 100) và đưa ra quyết định PASS (>= 75 điểm) hoặc FAIL (< 75 điểm).
    - Cung cấp phản hồi chi tiết (feedback) định hướng cho WritingAgent sửa đổi nếu cần.
    """
    def __init__(self):
        super().__init__(
            name="ReviewAgent",
            description="Thẩm định chất lượng báo cáo, kiểm tra độ phủ trích dẫn và phát hiện hallucination (UC010).",
            instruction="""Bạn là phản biện học thuật nghiêm khắc (Senior Academic Peer Reviewer).
            Nhiệm vụ: Thẩm định bản thảo Literature Review theo 3 tiêu chí:
            1. Tính chặt chẽ học thuật và tính hoàn thiện của cấu trúc.
            2. Độ phủ và tính chính xác của trích dẫn (phát hiện trích dẫn giả mạo).
            3. Phát hiện rủi ro hallucination hoặc các khẳng định thiếu căn cứ thực nghiệm.
            Đưa ra điểm số (0-100), trạng thái PASS/FAIL và phản hồi chi tiết để tác giả chỉnh sửa.""",
            tools=[retrieve_document_chunks]
        )

    async def run(
        self,
        db: AsyncSession,
        session_id: str,
        report_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Thực thi quy trình thẩm định báo cáo:
        1. Lấy báo cáo và danh sách trích dẫn hợp lệ trong phiên.
        2. Tính toán tỷ lệ bao phủ trích dẫn trong văn bản (Citation coverage).
        3. Dùng LLM phản biện, phát hiện ảo giác và chấm điểm.
        4. Lưu bản ghi Review và cập nhật review_status (PASS/FAIL) cho Report.
        """
        run = await self.log_start(
            db,
            session_id,
            step_description="Thẩm định chất lượng báo cáo và kiểm tra tính xác thực nguồn theo chuẩn ADK",
            input_data={"report_id": report_id}
        )

        try:
            # 1. Truy vấn báo cáo (Report) và danh sách trích dẫn (Citations)
            if report_id:
                stmt = select(Report).where(Report.id == report_id)
            else:
                stmt = select(Report).where(Report.session_id == session_id).order_by(desc(Report.version))

            res = await db.execute(stmt)
            report = res.scalar_one_or_none()
            if not report:
                raise ValueError(f"Report not found for session {session_id}.")

            c_stmt = select(Citation).where(Citation.session_id == session_id)
            c_res = await db.execute(c_stmt)
            citations = c_res.scalars().all()
            citation_keys = [c.citation_key for c in citations if c.citation_key]

            # 2. Phân tích độ bao phủ của trích dẫn trong nội dung báo cáo
            used_keys = [k for k in citation_keys if k in report.content]
            coverage = len(used_keys) / len(citation_keys) if citation_keys else 1.0

            # 3. Sử dụng LLM thẩm định ngang hàng (Peer Review) và kiểm tra ảo giác
            prompt = f"""You are a rigorous senior academic peer reviewer. Evaluate the following Literature Review draft.

Report Title: {report.title}
Report Content:
{report.content[:7000]}

Known Valid Citations: {", ".join(citation_keys)}

Review Criteria:
1. Academic rigor, flow, and structural completeness.
2. Citation coverage & grounding (Are claims properly cited? Are there fake citations?).
3. Detection of hallucinations or unfounded generalizations.

Output exact JSON format:
{{
  "score": 85.0,
  "status": "PASS",
  "issues": [
    {{"type": "citation_check", "description": "Good coverage", "severity": "low"}}
  ],
  "feedback": "Concise feedback for improvements...",
  "hallucination_risks": []
}}
Note: status must be "PASS" (score >= 75) or "FAIL" (score < 75).
"""
            review_data = await llm_service.generate_json(prompt)

            score = float(review_data.get("score", 88.0))
            # Nếu độ bao phủ trích dẫn dưới 50%, tự động hạ điểm và đánh dấu FAIL
            if coverage < 0.5:
                score = min(score, 60.0)
                review_data["status"] = "FAIL"
                review_data.setdefault("issues", []).append({
                    "type": "citation_coverage",
                    "description": f"Low citation coverage: only {int(coverage*100)}% of source papers cited.",
                    "severity": "high"
                })

            status = "PASS" if score >= 75.0 else "FAIL"

            # 4. Lưu bản ghi Review vào cơ sở dữ liệu
            review = Review(
                report_id=report.id,
                session_id=session_id,
                score=score,
                status=status,
                issues=review_data.get("issues", []),
                feedback=review_data.get("feedback", "Review completed successfully."),
                hallucination_risks=review_data.get("hallucination_risks", []),
                citation_coverage=coverage
            )
            db.add(review)

            # Cập nhật trạng thái thẩm định cho Report
            report.review_status = status
            await db.commit()
            await db.refresh(review)

            output = {
                "review_id": review.id,
                "report_id": report.id,
                "score": score,
                "status": status,
                "feedback": review.feedback,
                "citation_coverage": coverage,
                "issues": review.issues
            }

            await self.log_end(db, run, status="COMPLETED", output_data=output)
            return output

        except Exception as e:
            logger.error(f"[{self.name}] Error: {e}", exc_info=True)
            await self.log_end(db, run, status="FAILED", error_message=str(e))
            raise

# Khởi tạo singleton instance cho ReviewAgent
review_agent = ReviewAgent()

