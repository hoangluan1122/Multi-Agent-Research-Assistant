"""
Endpoint quản lý Phiên nghiên cứu (Sessions API - UC001).
Cung cấp các API RESTful cho phép khởi tạo, tra cứu, chỉnh sửa và xóa phiên nghiên cứu khoa học.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.session import ResearchSession
from app.models.paper import Paper
from app.models.report import Report
from app.models.user import User
from app.api.deps import get_current_user_optional
from app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionDetailResponse,
)

router = APIRouter(prefix="/sessions", tags=["Sessions (UC001)"])

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    UC001: Khởi tạo phiên nghiên cứu khoa học mới.
    - Nhận chủ đề (topic), câu hỏi nghiên cứu (research_question) và các tham số giới hạn.
    - Tự động liên kết phiên với tài khoản người dùng nếu đã đăng nhập.
    """
    params = payload.parameters or {}
    params.update({
        "year_start": payload.year_start,
        "year_end": payload.year_end,
        "max_papers": payload.max_papers,
        "sources": payload.sources,
        "citation_style": payload.citation_style,
    })

    session = ResearchSession(
        user_id=current_user.id if current_user else None,
        topic=payload.topic,
        research_question=payload.research_question,
        parameters=params,
        status="READY",
        current_step="INITIALIZED"
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy danh sách các phiên nghiên cứu gần nhất trong hệ thống.
    Nếu người dùng đã đăng nhập: Trả về các phiên của chính tài khoản đó.
    """
    stmt = select(ResearchSession).order_by(desc(ResearchSession.created_at)).limit(limit).offset(offset)
    if current_user:
        stmt = stmt.where(or_(ResearchSession.user_id == current_user.id, ResearchSession.user_id.is_(None)))
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Xem chi tiết thông tin của một phiên nghiên cứu:
    - Kèm theo số lượng bài báo (paper_count).
    - Kiểm tra xem phiên đã có báo cáo hoàn chỉnh chưa và lấy ID báo cáo mới nhất.
    """
    stmt = (
        select(ResearchSession)
        .where(ResearchSession.id == session_id)
        .options(selectinload(ResearchSession.papers), selectinload(ResearchSession.reports))
    )
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    latest_report = session.reports[-1] if session.reports else None

    return SessionDetailResponse(
        id=session.id,
        topic=session.topic,
        research_question=session.research_question,
        parameters=session.parameters or {},
        status=session.status,
        current_step=session.current_step,
        error_message=session.error_message,
        created_at=session.created_at,
        updated_at=session.updated_at,
        paper_count=len(session.papers),
        has_report=bool(session.reports),
        latest_report_id=latest_report.id if latest_report else None
    )

@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    payload: SessionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Cập nhật chủ đề, câu hỏi nghiên cứu hoặc tham số của một phiên đang tồn tại.
    """
    stmt = select(ResearchSession).where(ResearchSession.id == session_id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    if payload.topic is not None:
        session.topic = payload.topic
    if payload.research_question is not None:
        session.research_question = payload.research_question
    if payload.parameters is not None:
        session.parameters = payload.parameters

    await db.commit()
    await db.refresh(session)
    return session

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Xóa bỏ một phiên nghiên cứu và toàn bộ dữ liệu phụ thuộc liên quan (cascade).
    """
    stmt = select(ResearchSession).where(ResearchSession.id == session_id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    await db.delete(session)
    await db.commit()
    return None

