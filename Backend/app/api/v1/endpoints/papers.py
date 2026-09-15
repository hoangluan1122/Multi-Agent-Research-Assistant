"""
Endpoint quản lý Tài liệu Nghiên cứu (Papers API - UC002, UC003, UC004).
Hỗ trợ tìm kiếm học thuật (ArXiv/Semantic Scholar), tải lên tài liệu PDF, chọn lọc danh mục bài báo và kích hoạt phân tích sâu.
"""

import os
import shutil
import asyncio
from typing import List, Optional
try:
    import magic
except ImportError:
    magic = None
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.core.config import settings
from app.models.paper import Paper
from app.models.session import ResearchSession
from app.agents.search_agent import search_agent
from app.agents.reading_agent import reading_agent
from app.models.user import User
from app.api.deps import get_current_user_optional, verify_session_access
from app.services.academic_search import AcademicSearchError
from app.schemas.paper import (
    PaperSearchRequest,
    PaperResponse,
    PaperCreate,
    PaperSelectionUpdate,
)

from app.services.paper_translation import translate_content

router = APIRouter(prefix="/papers", tags=["Papers (UC002, UC003, UC004)"])

# @trace: REQ-001, REQ-002
@router.post("/search", response_model=List[PaperResponse])
async def search_academic_papers(
    payload: PaperSearchRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    UC002: Tìm kiếm tài liệu học thuật trực tuyến.
    - Kiểm tra quyền sở hữu phiên nghiên cứu.
    - Kích hoạt SearchAgent truy vấn từ ArXiv và Semantic Scholar.
    - Lọc điểm tương đồng ngữ nghĩa và lưu vào bảng `papers`.
    - Trả về danh sách toàn bộ các bài báo thuộc phiên nghiên cứu.
    """
    stmt = select(ResearchSession).where(ResearchSession.id == payload.session_id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    verify_session_access(session, current_user)

    # @trace: REQ-036
    if payload.clear_existing:
        old_stmt = select(Paper).where(Paper.session_id == payload.session_id)
        old_res = await db.execute(old_stmt)
        for old_paper in old_res.scalars().all():
            if old_paper.pdf_path and os.path.exists(old_paper.pdf_path):
                try:
                    os.remove(old_paper.pdf_path)
                except OSError:
                    pass
            await db.delete(old_paper)
        await db.flush()

    try:
        search_result = await search_agent.run(
            db=db,
            session_id=payload.session_id,
            query=payload.query,
            year_start=payload.year_start,
            year_end=payload.year_end,
            max_papers=payload.max_results or 10,
            sources=payload.sources
        )
    except AcademicSearchError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e)) from e

    paper_ids = [item["id"] for item in search_result.get("papers", []) if item.get("id")]
    if not paper_ids:
        return []

    # Trả về đúng batch bài báo của lần tìm kiếm hiện tại kèm phân tích
    p_stmt = (
        select(Paper)
        .where(Paper.id.in_(paper_ids))
        .options(selectinload(Paper.analysis))
    )
    p_res = await db.execute(p_stmt)
    papers_by_id = {paper.id: paper for paper in p_res.scalars().all()}
    return [papers_by_id[paper_id] for paper_id in paper_ids if paper_id in papers_by_id]

# @trace: REQ-001, REQ-002
@router.post("/upload", response_model=PaperResponse)
async def upload_paper_pdf(
    session_id: str = Form(...),
    title: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    UC003: Tải lên tệp PDF bài báo trực tiếp từ máy tính người dùng.
    - Kiểm tra quyền sở hữu phiên nghiên cứu.
    - Lưu file vào thư mục `uploads/{session_id}/`.
    - Tạo bản ghi Paper mới với nguồn là `upload` và gán trạng thái PENDING.
    """
    stmt = select(ResearchSession).where(ResearchSession.id == session_id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    verify_session_access(session, current_user)

    # 1. Kiểm tra phần mở rộng tên file
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported (invalid file extension)")

    # 2. Đọc header bytes để xác thực định dạng thực tế (Magic Bytes)
    header = await file.read(2048)
    await file.seek(0)  # Đặt lại con trỏ file về đầu để lưu trữ trọn vẹn sau đó

    # Kiểm tra MIME type thông qua python-magic hoặc magic bytes header
    if magic:
        mime_type = magic.from_buffer(header, mime=True)
        if mime_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format: Detected '{mime_type}', expected 'application/pdf'"
            )
    else:
        if not header.startswith(b"%PDF"):
            raise HTTPException(
                status_code=400,
                detail="Invalid file format: File does not have valid PDF header bytes"
            )

    # Lưu file PDF vào ổ đĩa cục bộ
    session_upload_dir = os.path.join(settings.UPLOAD_DIR, session_id)
    os.makedirs(session_upload_dir, exist_ok=True)
    file_path = os.path.join(session_upload_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    paper_title = title or file.filename.replace(".pdf", "").replace("_", " ")

    paper = Paper(
        session_id=session_id,
        title=paper_title,
        authors=["Author"],
        abstract="Uploaded PDF Document",
        year=2024,
        venue="Direct Upload",
        pdf_path=file_path,
        source="upload",
        relevance_score=1.0,
        is_selected=True,
        ingestion_status="PENDING"
    )
    db.add(paper)
    await db.commit()
    await db.refresh(paper)
    paper.analysis = None
    return paper

# @trace: REQ-001, REQ-002
@router.get("/session/{session_id}", response_model=List[PaperResponse])
async def get_session_papers(
    session_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy danh sách toàn bộ các bài báo khoa học đã được tìm thấy hoặc tải lên trong một phiên.
    Kiểm tra quyền truy cập phiên (không xem nhầm bài báo của người khác).
    """
    stmt = select(ResearchSession).where(ResearchSession.id == session_id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    verify_session_access(session, current_user)

    p_stmt = (
        select(Paper)
        .where(Paper.session_id == session_id)
        .options(selectinload(Paper.analysis))
    )
    p_res = await db.execute(p_stmt)
    return p_res.scalars().all()

@router.post("/selection", status_code=status.HTTP_200_OK)
async def update_paper_selection(payload: PaperSelectionUpdate, db: AsyncSession = Depends(get_db)):
    """
    Cập nhật cờ chọn lọc (is_selected = True/False) cho danh sách các bài báo.
    Chỉ các bài báo được chọn mới tham gia vào bước Đọc sâu, Soạn thảo và Báo cáo.
    """
    stmt = select(Paper).where(Paper.id.in_(payload.paper_ids))
    res = await db.execute(stmt)
    papers = res.scalars().all()
    for p in papers:
        p.is_selected = payload.is_selected
    await db.commit()
    return {"message": f"Updated selection for {len(papers)} papers"}

@router.post("/{paper_id}/analyze", response_model=PaperResponse)
async def analyze_single_paper(paper_id: str, db: AsyncSession = Depends(get_db)):
    """
    UC004, UC005: Kích hoạt ReadingAgent phân tích sâu cấu trúc cho một bài báo cụ thể.
    - Đọc PDF hoặc Abstract, trích xuất 5 khía cạnh cốt lõi và lưu vector vào Qdrant.
    """
    stmt = select(Paper).where(Paper.id == paper_id).options(selectinload(Paper.analysis))
    res = await db.execute(stmt)
    paper = res.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    await reading_agent.run(db=db, session_id=paper.session_id, paper_ids=[paper_id])

    await db.refresh(paper)
    return paper

@router.post("/{paper_id}/translate", response_model=PaperResponse)
async def translate_single_paper(paper_id: str, db: AsyncSession = Depends(get_db)):
    """
    Dịch tiêu đề và tóm tắt (Abstract) của bài báo sang Tiếng Việt chuẩn mực.
    """
    stmt = select(Paper).where(Paper.id == paper_id).options(selectinload(Paper.analysis))
    res = await db.execute(stmt)
    paper = res.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    try:
        translated = await translate_content(paper.title, paper.abstract)
        if translated.get("title_vi"):
            paper.title = translated["title_vi"]
        if translated.get("abstract_vi"):
            paper.abstract = translated["abstract_vi"]
        await db.commit()
        await db.refresh(paper)
    except asyncio.TimeoutError:
        await db.rollback()
        raise HTTPException(status_code=504, detail="Dịch quá thời gian chờ. Vui lòng thử lại.")
    except (RuntimeError, ValueError) as e:
        await db.rollback()
        raise HTTPException(status_code=502, detail=str(e))

    return paper

@router.post("/session/{session_id}/translate-all", response_model=List[PaperResponse])
async def translate_all_session_papers(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Dịch toàn bộ tiêu đề và tóm tắt của tất cả bài báo trong phiên sang Tiếng Việt.
    """
    stmt = (
        select(Paper)
        .where(Paper.session_id == session_id)
        .options(selectinload(Paper.analysis))
    )
    res = await db.execute(stmt)
    papers = res.scalars().all()
    if not papers:
        return []

    semaphore = asyncio.Semaphore(3)

    async def translate_one(paper):
        async with semaphore:
            return await translate_content(paper.title, paper.abstract)

    # Complete every translation before mutating any rows: no false partial success.
    tasks = [asyncio.create_task(translate_one(paper)) for paper in papers]
    try:
        translations = await asyncio.wait_for(asyncio.gather(*tasks), timeout=50)
    except Exception as exc:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await db.rollback()
        detail = ("Dịch quá thời gian chờ. Hãy dịch từng bài hoặc thử lại."
                  if isinstance(exc, asyncio.TimeoutError)
                  else "Không thể dịch toàn bộ bài báo. Chưa lưu thay đổi; vui lòng thử dịch từng bài.")
        raise HTTPException(status_code=502, detail=detail) from exc

    for paper, translated in zip(papers, translations):
        paper.title = translated["title_vi"]
        if paper.abstract:
            paper.abstract = translated["abstract_vi"]

    await db.commit()
    for p in papers:
        await db.refresh(p)
    return papers


# @trace: REQ-035
@router.delete("/session/{session_id}")
async def clear_session_papers(
    session_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Xóa toàn bộ bài báo trong một phiên nghiên cứu (Clear All Papers in Session).
    """
    stmt = select(ResearchSession).where(ResearchSession.id == session_id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    verify_session_access(session, current_user)

    papers_stmt = select(Paper).where(Paper.session_id == session_id)
    p_res = await db.execute(papers_stmt)
    papers = p_res.scalars().all()

    count = len(papers)
    for paper in papers:
        if paper.pdf_path and os.path.exists(paper.pdf_path):
            try:
                os.remove(paper.pdf_path)
            except OSError:
                pass
        await db.delete(paper)

    await db.commit()
    return {"message": f"Đã xóa toàn bộ {count} bài báo trong phiên.", "deleted_count": count}


# @trace: REQ-034
@router.delete("/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_paper(
    paper_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Xóa một bài báo đơn lẻ khỏi phiên nghiên cứu.
    """
    stmt = (
        select(Paper)
        .where(Paper.id == paper_id)
        .options(selectinload(Paper.session))
    )
    res = await db.execute(stmt)
    paper = res.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    if paper.session:
        verify_session_access(paper.session, current_user)

    if paper.pdf_path and os.path.exists(paper.pdf_path):
        try:
            os.remove(paper.pdf_path)
        except OSError:
            pass

    await db.delete(paper)
    await db.commit()
    return None


