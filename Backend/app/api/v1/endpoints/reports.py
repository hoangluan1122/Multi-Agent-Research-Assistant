"""
Endpoint quản lý Báo cáo & Xuất bản (Reports & Export API - UC009, UC010, UC012).
Cung cấp API tra cứu bản thảo báo cáo Literature Review, lịch sử review chấm điểm, danh mục trích dẫn và xuất file (.md, .docx, .pdf).
"""

import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.report import Report, Review
from app.models.citation import Citation
from app.models.session import ResearchSession
from app.services.export_service import export_service
from app.schemas.report import (
    ReportResponse,
    ReviewResponse,
    CitationResponse,
    ExportRequest,
)

router = APIRouter(prefix="/reports", tags=["Reports & Export (UC009, UC010, UC012)"])

@router.get("/session/{session_id}", response_model=List[ReportResponse])
async def get_session_reports(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Lấy danh sách toàn bộ các phiên bản báo cáo (Report Versions) của một phiên nghiên cứu.
    Bao gồm thông tin bảng so sánh đối chiếu và lịch sử đánh giá phản biện (reviews).
    """
    stmt = (
        select(Report)
        .where(Report.session_id == session_id)
        .options(selectinload(Report.reviews))
        .order_by(desc(Report.version))
    )
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report_detail(report_id: str, db: AsyncSession = Depends(get_db)):
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
    return report

@router.get("/{report_id}/citations", response_model=List[CitationResponse])
async def get_report_citations(report_id: str, db: AsyncSession = Depends(get_db)):
    """
    Lấy danh mục các tài liệu trích dẫn tham khảo chuẩn hóa (Citation list) gắn liền với báo cáo.
    """
    stmt = select(Report).where(Report.id == report_id)
    res = await db.execute(stmt)
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    c_stmt = select(Citation).where(Citation.session_id == report.session_id)
    c_res = await db.execute(c_stmt)
    return c_res.scalars().all()

@router.post("/{report_id}/export")
async def export_report_file(
    report_id: str,
    payload: ExportRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    UC012: Xuất bản và tải về file báo cáo nghiên cứu hoàn chỉnh.
    Hỗ trợ 3 định dạng:
    - `markdown`: File .md nguyên bản kèm cấu trúc chuẩn.
    - `docx`: File Microsoft Word (.docx) được tạo động qua python-docx.
    - `pdf`: File PDF chuẩn in ấn qua WeasyPrint hoặc ReportLab.
    """
    stmt = select(Report).where(Report.id == report_id)
    res = await db.execute(stmt)
    report = res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

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

