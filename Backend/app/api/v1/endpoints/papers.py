"""
Endpoint quản lý Tài liệu Nghiên cứu (Papers API - UC002, UC003, UC004).
Hỗ trợ tìm kiếm học thuật (ArXiv/Semantic Scholar), tải lên tài liệu PDF, chọn lọc danh mục bài báo và kích hoạt phân tích sâu.
"""

import os
import shutil
from typing import List, Optional
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
from app.schemas.paper import (
    PaperSearchRequest,
    PaperResponse,
    PaperCreate,
    PaperSelectionUpdate,
)

from app.services.llm_service import llm_service

router = APIRouter(prefix="/papers", tags=["Papers (UC002, UC003, UC004)"])

@router.post("/search", response_model=List[PaperResponse])
async def search_academic_papers(
    payload: PaperSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    UC002: Tìm kiếm tài liệu học thuật trực tuyến.
    - Kích hoạt SearchAgent truy vấn từ ArXiv và Semantic Scholar.
    - Lọc điểm tương đồng ngữ nghĩa và lưu vào bảng `papers`.
    - Trả về danh sách toàn bộ các bài báo thuộc phiên nghiên cứu.
    """
    stmt = select(ResearchSession).where(ResearchSession.id == payload.session_id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    await search_agent.run(
        db=db,
        session_id=payload.session_id,
        query=payload.query,
        year_start=payload.year_start,
        year_end=payload.year_end,
        max_papers=payload.max_results,
        sources=payload.sources
    )

    # Trả về danh sách bài báo đã cập nhật kèm phân tích
    p_stmt = (
        select(Paper)
        .where(Paper.session_id == payload.session_id)
        .options(selectinload(Paper.analysis))
    )
    p_res = await db.execute(p_stmt)
    return p_res.scalars().all()

@router.post("/upload", response_model=PaperResponse)
async def upload_paper_pdf(
    session_id: str = Form(...),
    title: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    UC003: Tải lên tệp PDF bài báo trực tiếp từ máy tính người dùng.
    - Lưu file vào thư mục `uploads/{session_id}/`.
    - Tạo bản ghi Paper mới với nguồn là `upload` và gán trạng thái PENDING.
    """
    stmt = select(ResearchSession).where(ResearchSession.id == session_id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

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

@router.get("/session/{session_id}", response_model=List[PaperResponse])
async def get_session_papers(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Lấy danh sách toàn bộ các bài báo khoa học đã được tìm thấy hoặc tải lên trong một phiên.
    """
    stmt = (
        select(Paper)
        .where(Paper.session_id == session_id)
        .options(selectinload(Paper.analysis))
    )
    res = await db.execute(stmt)
    return res.scalars().all()

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

    prompt = f"""You are a professional scientific translator and researcher.
Translate the following academic paper title and abstract into natural, accurate, and high-quality Vietnamese (Tiếng Việt).

Paper Title (EN): {paper.title}
Abstract (EN): {paper.abstract or 'No abstract provided'}

Respond strictly in JSON format:
{{
  "title_vi": "Tiêu đề tiếng Việt chuẩn xác",
  "abstract_vi": "Tóm tắt abstract tiếng Việt trôi chảy, chuẩn thuật ngữ chuyên ngành"
}}
"""
    try:
        translated = await llm_service.generate_json(prompt)
        if translated.get("title_vi"):
            paper.title = translated["title_vi"]
        if translated.get("abstract_vi"):
            paper.abstract = translated["abstract_vi"]
        await db.commit()
        await db.refresh(paper)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

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

    for paper in papers:
        prompt = f"""You are a professional scientific translator and researcher.
Translate the following academic paper title and abstract into natural, accurate, and high-quality Vietnamese (Tiếng Việt).

Paper Title (EN): {paper.title}
Abstract (EN): {paper.abstract or 'No abstract provided'}

Respond strictly in JSON format:
{{
  "title_vi": "Tiêu đề tiếng Việt chuẩn xác",
  "abstract_vi": "Tóm tắt abstract tiếng Việt trôi chảy, chuẩn thuật ngữ chuyên ngành"
}}
"""
        try:
            translated = await llm_service.generate_json(prompt)
            if translated.get("title_vi"):
                paper.title = translated["title_vi"]
            if translated.get("abstract_vi"):
                paper.abstract = translated["abstract_vi"]
        except Exception:
            continue

    await db.commit()
    for p in papers:
        await db.refresh(p)
    return papers

