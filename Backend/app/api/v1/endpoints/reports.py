"""
Endpoint quản lý Báo cáo & Xuất bản (Reports & Export API - UC009, UC010, UC012).
Cung cấp API tra cứu bản thảo báo cáo Literature Review, lịch sử review chấm điểm, danh mục trích dẫn và xuất file (.md, .docx, .pdf).
"""

import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.report import Report, Review
from app.models.citation import Citation
from app.models.session import ResearchSession
from app.models.user import User
from app.api.deps import get_current_user_optional, verify_session_access
from app.services.export_service import export_service
from app.schemas.report import (
    ReportResponse,
    ReviewResponse,
    CitationResponse,
    ExportRequest,
    ReportReviseRequest,
)

router = APIRouter(prefix="/reports", tags=["Reports & Export (UC009, UC010, UC012)"])

# @trace: REQ-002, REQ-006
@router.get("/session/{session_id}", response_model=List[ReportResponse])
async def get_session_reports(
    session_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy danh sách toàn bộ các phiên bản báo cáo (Report Versions) của một phiên nghiên cứu.
    Bao gồm thông tin bảng so sánh đối chiếu và lịch sử đánh giá phản biện (reviews).
    """
    s_stmt = select(ResearchSession).where(ResearchSession.id == session_id)
    s_res = await db.execute(s_stmt)
    session = s_res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    verify_session_access(session, current_user)

    stmt = (
        select(Report)
        .where(Report.session_id == session_id)
        .options(selectinload(Report.reviews))
        .order_by(desc(Report.version))
    )
    res = await db.execute(stmt)
    return res.scalars().all()

# @trace: REQ-002, REQ-006
@router.get("/{report_id}", response_model=ReportResponse)
async def get_report_detail(
    report_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Xem chi tiết toàn văn nội dung một báo cáo cụ thể (Markdown content, Outline, Review scorecard).
    """
    stmt = (
        select(Report)
        .where(Report.id == report_id)
        .options(selectinload(Report.reviews))
    )
    res = await db.execute(stmt)
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    s_stmt = select(ResearchSession).where(ResearchSession.id == report.session_id)
    s_res = await db.execute(s_stmt)
    session = s_res.scalar_one_or_none()
    if session:
        verify_session_access(session, current_user)

    return report

# @trace: REQ-002, REQ-006
@router.get("/{report_id}/citations", response_model=List[CitationResponse])
async def get_report_citations(
    report_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy danh mục các tài liệu trích dẫn tham khảo chuẩn hóa (Citation list) gắn liền với báo cáo.
    """
    stmt = select(Report).where(Report.id == report_id)
    res = await db.execute(stmt)
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    s_stmt = select(ResearchSession).where(ResearchSession.id == report.session_id)
    s_res = await db.execute(s_stmt)
    session = s_res.scalar_one_or_none()
    if session:
        verify_session_access(session, current_user)

    c_stmt = select(Citation).where(Citation.session_id == report.session_id)
    c_res = await db.execute(c_stmt)
    return c_res.scalars().all()

# @trace: REQ-002, REQ-005, REQ-006
@router.post("/{report_id}/export")
async def export_report_file(
    report_id: str,
    payload: ExportRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    UC012: Xuất bản và tải về file báo cáo nghiên cứu hoàn chỉnh.
    Điều kiện xuất báo cáo:
    1. Kiểm tra quyền sở hữu phiên nghiên cứu (Multi-user Isolation).
    2. Báo cáo bắt buộc phải đạt tiêu chuẩn thẩm định (review_status == 'PASS').
    """
    stmt = select(Report).where(Report.id == report_id)
    res = await db.execute(stmt)
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    s_stmt = select(ResearchSession).where(ResearchSession.id == report.session_id)
    s_res = await db.execute(s_stmt)
    session = s_res.scalar_one_or_none()
    if session:
        verify_session_access(session, current_user)

    # Kiểm tra điều kiện thẩm định chất lượng (PASS-only)
    if report.review_status != "PASS":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Báo cáo chưa đạt tiêu chuẩn thẩm định chất lượng (Trạng thái hiện tại: {report.review_status}). Chỉ các báo cáo có kết quả PASS mới đủ điều kiện xuất bản."
        )

    format_choice = payload.format.lower()
    file_path = None
    media_type = "text/plain"

    if format_choice == "docx":
        file_path = export_service.export_docx(report.title, report.content, report.session_id)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif format_choice == "pdf":
        file_path = export_service.export_pdf(report.title, report.content, report.session_id)
        media_type = "application/pdf"
    else:  # markdown
        file_path = export_service.export_markdown(report.title, report.content, report.session_id)
        media_type = "text/markdown"

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=500, detail="Failed to render export document")

    filename = os.path.basename(file_path)
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )

@router.post("/{report_id}/revise", response_model=ReportResponse)
async def revise_report_with_feedback(
    report_id: str,
    payload: ReportReviseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    UC011: Chỉnh sửa và soạn thảo lại báo cáo dựa trên góp ý / feedback cụ thể của người dùng.
    - Lấy thông tin bản thảo hiện tại và số phiên bản.
    - Gọi WritingAgent thực hiện sửa đổi với feedback của người dùng để tạo Version mới (version = n + 1).
    - Tự động kích hoạt ReviewAgent để chấm điểm và kiểm tra độ bao phủ trích dẫn cho bản mới.
    """
    stmt = (
        select(Report)
        .where(Report.id == report_id)
        .options(selectinload(Report.reviews))
    )
    res = await db.execute(stmt)
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    from app.agents.writing_agent import writing_agent
    from app.agents.review_agent import review_agent

    # 1. Soạn thảo bản mới dựa trên feedback
    next_version = report.version + 1
    writing_res = await writing_agent.run(
        db=db,
        session_id=report.session_id,
        comparison_table=report.comparison_table,
        feedback=payload.feedback,
        version=next_version
    )
    new_report_id = writing_res["report_id"]

    # 2. Thẩm định chất lượng bản thảo mới
    await review_agent.run(
        db=db,
        session_id=report.session_id,
        report_id=new_report_id
    )

    # 3. Trả về báo cáo phiên bản mới hoàn chỉnh
    new_stmt = (
        select(Report)
        .where(Report.id == new_report_id)
        .options(selectinload(Report.reviews))
    )
    new_res = await db.execute(new_stmt)
    return new_res.scalar_one()


