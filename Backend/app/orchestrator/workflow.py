"""
Động cơ Điều phối Quy trình Nghiên cứu Khoa học Tự động (ResearchWorkflowEngine).
Tổ chức và điều phối tuần tự 6 bước cốt lõi theo đúng đặc tả yêu cầu phần mềm (SRS):
- Bước 1: SearchAgent (Tìm kiếm tài liệu học thuật - UC002).
- Bước 2: ReadingAgent (Đọc PDF, trích xuất cấu trúc & lập chỉ mục Vector RAG - UC004, UC005).
- Bước 3: SummarizationAgent (Tổng hợp & tạo ma trận so sánh - UC006, UC007).
- Bước 4: CitationAgent (Chuẩn hóa trích dẫn IEEE/APA - UC008).
- Bước 5 & 6: Vòng lặp Soạn thảo (WritingAgent - UC009, UC011) & Thẩm định (ReviewAgent - UC010) cho đến khi đạt PASS hoặc hết số lần thử.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.models.session import ResearchSession
from app.models.paper import Paper
from app.models.report import Report
from app.agents.search_agent import search_agent
from app.agents.reading_agent import reading_agent
from app.agents.summarization_agent import summarization_agent
from app.agents.citation_agent import citation_agent
from app.agents.writing_agent import writing_agent
from app.agents.review_agent import review_agent
from app.orchestrator.state import workflow_broadcaster
from app.core.config import settings

logger = logging.getLogger("paperflow.orchestrator")

class ResearchWorkflowEngine:
    """
    Động cơ thực thi chu trình Multi-Agent khép kín:
    - Quản lý phiên cơ sở dữ liệu AsyncSession độc lập cho toàn bộ tiến trình nền.
    - Cập nhật trạng thái session_id và phát thông báo SSE tới giao diện Frontend tại từng chặng.
    - Xử lý vòng lặp phản biện - viết lại (Writing & Review Loop) để loại bỏ rủi ro hallucination.
    """
    async def run_full_workflow(
        self,
        session_id: str,
        auto_search: bool = True,
        max_papers: int = 5,
        citation_style: str = "IEEE"
    ):
        """
        Khởi chạy toàn bộ luồng Multi-Agent cho Session theo đúng quy trình nghiệp vụ:
        1. Cập nhật trạng thái phiên thành RUNNING.
        2. Bước 1: Chạy SearchAgent để tìm kiếm các bài báo khoa học liên quan.
        3. Bước 2: Chạy ReadingAgent để bóc tách thông tin và nhúng vector RAG vào Qdrant.
        4. Bước 3: Chạy SummarizationAgent để xây dựng bảng ma trận so sánh.
        5. Bước 4: Chạy CitationAgent để định dạng danh mục tài liệu tham khảo.
        6. Bước 5-6: Chạy WritingAgent và ReviewAgent lặp lại nếu chưa đạt PASS.
        7. Hoàn tất và cập nhật trạng thái COMPLETED.
        """
        async with AsyncSessionLocal() as db:
            try:
                # 1. Kiểm tra sự tồn tại của phiên nghiên cứu
                stmt = select(ResearchSession).where(ResearchSession.id == session_id)
                res = await db.execute(stmt)
                session = res.scalar_one_or_none()
                if not session:
                    logger.error(f"Session {session_id} not found.")
                    return

                session.status = "RUNNING"
                session.current_step = "STARTING_WORKFLOW"
                await db.commit()

                await self._notify(session_id, "RUNNING", "STARTING", 5, "Khởi động chu trình nghiên cứu Multi-Agent", "System")

                # =========================================================================
                # BƯỚC 1: Search Agent (Tìm kiếm tài liệu học thuật - UC002)
                # =========================================================================
                p_stmt = select(Paper).where(Paper.session_id == session_id)
                p_res = await db.execute(p_stmt)
                existing_papers = p_res.scalars().all()

                if auto_search or not existing_papers:
                    await self._notify(session_id, "RUNNING", "SEARCHING_PAPERS", 15, "SearchAgent đang tìm kiếm tài liệu học thuật...", "SearchAgent")
                    search_res = await search_agent.run(
                        db=db,
                        session_id=session_id,
                        max_papers=max_papers
                    )
                    await self._notify(session_id, "RUNNING", "SEARCH_COMPLETED", 30, f"Đã tìm thấy và lọc {search_res['total_found']} bài báo liên quan.", "SearchAgent")

                # @trace: REQ-024
                # Circuit Breaker: Kiểm tra danh sách bài báo trong cơ sở dữ liệu
                # Nếu không có bài báo nào, lập tức dừng workflow và báo FAILED minh bạch
                check_stmt = select(func.count(Paper.id)).where(Paper.session_id == session_id)
                total_papers_in_db = (await db.execute(check_stmt)).scalar() or 0
                if total_papers_in_db == 0:
                    error_msg = (
                        "Không tìm thấy tài liệu khoa học nào phù hợp với chủ đề nghiên cứu. "
                        "Vui lòng mở rộng từ khóa tìm kiếm hoặc tải lên file PDF bài báo."
                    )
                    logger.warning(f"Workflow stopped for session {session_id}: 0 papers found.")
                    session.status = "FAILED"
                    session.current_step = "SEARCH_NO_PAPERS"
                    session.error_message = error_msg
                    await db.commit()
                    await self._notify(session_id, "FAILED", "SEARCH_NO_PAPERS", 30, error_msg, "SearchAgent")
                    return

                # =========================================================================
                # BƯỚC 2: Reading Agent (Đọc tài liệu, trích xuất cấu trúc & Vector RAG - UC004, UC005)
                # =========================================================================
                await self._notify(session_id, "RUNNING", "READING_AND_EMBEDDING", 45, "ReadingAgent đang đọc, bóc tách cấu trúc và tạo Vector RAG...", "ReadingAgent")
                reading_res = await reading_agent.run(
                    db=db,
                    session_id=session_id
                )
                await self._notify(session_id, "RUNNING", "READING_COMPLETED", 60, f"Đã bóc tách thành công {reading_res['analyzed_count']} bài báo vào cơ sở tri thức.", "ReadingAgent")

                # @trace: REQ-024
                # Circuit Breaker: Kiểm tra xem có ít nhất 1 bài báo được đọc / bóc tách thành công không
                analyzed_count = reading_res.get("analyzed_count", 0)
                if analyzed_count == 0:
                    check_analysis = select(func.count(Paper.id)).where(
                        Paper.session_id == session_id,
                        Paper.ingestion_status == "completed"
                    )
                    total_analyzed = (await db.execute(check_analysis)).scalar() or 0
                    if total_analyzed == 0:
                        error_msg = (
                            "Không thể bóc tách cấu trúc từ các bài báo đã chọn. "
                            "Vui lòng kiểm tra lại tài liệu hoặc tải lên file PDF hợp lệ."
                        )
                        logger.warning(f"Workflow stopped for session {session_id}: 0 papers analyzed.")
                        session.status = "FAILED"
                        session.current_step = "READING_FAILED"
                        session.error_message = error_msg
                        await db.commit()
                        await self._notify(session_id, "FAILED", "READING_FAILED", 60, error_msg, "ReadingAgent")
                        return

                # =========================================================================
                # BƯỚC 3: Summarization Agent (Tổng hợp & Tạo bảng so sánh đối chiếu - UC006, UC007)
                # =========================================================================
                await self._notify(session_id, "RUNNING", "SUMMARIZING_AND_COMPARING", 65, "SummarizationAgent đang tổng hợp và lập ma trận so sánh...", "SummarizationAgent")
                summary_res = await summarization_agent.run(
                    db=db,
                    session_id=session_id
                )
                comp_table = summary_res.get("comparison_table", "")
                synthesized_summary = summary_res.get("synthesized_summary", "")

                # =========================================================================
                # BƯỚC 4 & 5: Vòng lặp Soạn thảo & Thẩm định phản biện (Writing & Review Loop - UC009, UC010, UC011)
                # =========================================================================
                retry_count = 0
                max_retries = settings.MAX_REVIEW_RETRIES
                is_passed = False
                latest_report_id = None
                feedback = None

                # @trace: REQ-003
                # Xác định số version tiếp theo từ DB để đảm bảo không bao giờ trùng lặp version
                max_v_stmt = select(func.max(Report.version)).where(Report.session_id == session_id)
                current_max_v = (await db.execute(max_v_stmt)).scalar() or 0
                current_version = current_max_v

                while retry_count <= max_retries and not is_passed:
                    current_version += 1
                    version = current_version
                    await self._notify(
                        session_id,
                        "RUNNING",
                        "WRITING_DRAFT",
                        75,
                        f"WritingAgent đang soạn thảo Literature Review (Bản #{version})...",
                        "WritingAgent"
                    )

                    # Viết báo cáo
                    writing_res = await writing_agent.run(
                        db=db,
                        session_id=session_id,
                        comparison_table=comp_table,
                        synthesized_summary=synthesized_summary,
                        feedback=feedback,
                        version=version
                    )
                    latest_report_id = writing_res["report_id"]

                    # Thẩm định phản biện chất lượng
                    await self._notify(
                        session_id,
                        "REVIEWING",
                        "REVIEWING_REPORT",
                        85,
                        f"ReviewAgent đang thẩm định độ tin cậy và kiểm tra hallucination...",
                        "ReviewAgent"
                    )

                    review_res = await review_agent.run(
                        db=db,
                        session_id=session_id,
                        report_id=latest_report_id
                    )

                    if review_res["status"] == "PASS":
                        is_passed = True
                        break
                    else:
                        retry_count += 1
                        # feedback = review_res.get("feedback")
                        feedback = review_res.get("feedback") or "Bổ sung phân tích, kiểm tra lại trích dẫn và cải thiện báo cáo."
                        await self._notify(
                            session_id,
                            "RUNNING",
                            "REVISING_WORKFLOW",
                            70,
                            f"ReviewAgent yêu cầu sửa: {feedback[:100]}... (Thực hiện lần sửa {retry_count}/{max_retries})",
                            "ReviewAgent"
                        )

                # =========================================================================
                # BƯỚC 6: Citation Agent (Quản lý và định dạng trích dẫn chuẩn - UC008)
                # =========================================================================
                await self._notify(session_id, "RUNNING", "FORMATTING_CITATIONS", 95, f"CitationAgent đang kiểm chứng và định dạng danh mục trích dẫn {citation_style}...", "CitationAgent")
                await citation_agent.run(
                    db=db,
                    session_id=session_id,
                    style=citation_style
                )

                # Cập nhật trạng thái hoàn thành phiên
                session.status = "COMPLETED"
                session.current_step = "COMPLETED"
                await db.commit()

                await self._notify(
                    session_id,
                    "COMPLETED",
                    "COMPLETED",
                    100,
                    "Báo cáo nghiên cứu khoa học đã hoàn tất thành công!",
                    "System",
                    extra={"report_id": latest_report_id}
                )

            except Exception as e:
                logger.error(f"Workflow error for session {session_id}: {e}", exc_info=True)
                try:
                    stmt = select(ResearchSession).where(ResearchSession.id == session_id)
                    res = await db.execute(stmt)
                    s = res.scalar_one_or_none()
                    if s:
                        s.status = "FAILED"
                        s.error_message = str(e)
                        await db.commit()
                except Exception:
                    pass

                await self._notify(
                    session_id,
                    "FAILED",
                    "ERROR",
                    0,
                    f"Quy trình gặp lỗi: {str(e)}",
                    "System",
                    error=str(e)
                )

    async def _notify(
        self,
        session_id: str,
        status: str,
        current_step: str,
        progress: int,
        message: str,
        current_agent: str,
        error: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ):
        """Hàm nội bộ đóng gói payload và phát sự kiện SSE tới client theo dõi qua workflow_broadcaster."""
        
        async with AsyncSessionLocal() as status_db:
            stmt = select(ResearchSession).where(
                ResearchSession.id == session_id
            )
            res = await status_db.execute(stmt)
            status_session = res.scalar_one_or_none()

            if status_session:
                status_session.status = (
                    status if status in {"COMPLETED", "FAILED"} else "RUNNING"
                )
                status_session.current_step = current_step
                status_session.error_message = error
                await status_db.commit()

        payload = {
            "session_id": session_id,
            "status": status,
            "current_step": current_step,
            "progress": progress,
            "message": message,
            "current_agent": current_agent,
            "error": error,
            **(extra or {})
        }
        await workflow_broadcaster.broadcast(session_id, payload)

# Khởi tạo singleton instance cho ResearchWorkflowEngine
workflow_engine = ResearchWorkflowEngine()

