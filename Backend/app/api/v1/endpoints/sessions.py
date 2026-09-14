"""
Endpoint quản lý Phiên nghiên cứu (Sessions API - UC001).
Cung cấp các API RESTful cho phép khởi tạo, tra cứu, chỉnh sửa và xóa phiên nghiên cứu khoa học.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.core.config import settings
from app.models.session import ResearchSession
from app.models.paper import Paper
from app.models.report import Report
from app.models.user import User
from app.api.deps import get_current_user_optional, verify_session_access
from app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionDetailResponse,
)

router = APIRouter(prefix="/sessions", tags=["Sessions (UC001)"])

# @trace: REQ-008
@router.get("/guest/quota")
async def get_guest_quota(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    REQ-008: Kiểm tra hạn mức lượt dùng thử còn lại của khách.
    Nếu đã đăng nhập: Trả về is_logged_in=True (không giới hạn).
    """
    if current_user:
        return {
            "is_logged_in": True,
            "used": 0,
            "max": settings.GUEST_MAX_SESSIONS,
            "remaining": 999999,
            "is_exceeded": False
        }
    
    forwarded = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = "127.0.0.1"

    stmt = select(func.count(ResearchSession.id)).where(
        ResearchSession.user_id.is_(None),
        ResearchSession.client_ip == client_ip
    )
    res = await db.execute(stmt)
    used = res.scalar() or 0
    remaining = max(0, settings.GUEST_MAX_SESSIONS - used)

    return {
        "is_logged_in": False,
        "used": used,
        "max": settings.GUEST_MAX_SESSIONS,
        "remaining": remaining,
        "is_exceeded": used >= settings.GUEST_MAX_SESSIONS
    }

# @trace: REQ-001, REQ-002, REQ-008
@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    UC001: Khởi tạo phiên nghiên cứu khoa học mới.
    - Nhận chủ đề (topic), câu hỏi nghiên cứu (research_question) và các tham số giới hạn.
    - REQ-008: Kiểm soát hạn mức 2 phiên trải nghiệm cho khách vãng lai (Guest Mode).
    - Tự động liên kết phiên với tài khoản người dùng nếu đã đăng nhập.
    """
    client_ip = None
    if not current_user:
        # Trích xuất IP khách vãng lai từ header X-Forwarded-For hoặc client host
        forwarded = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = "127.0.0.1"

        # @trace: REQ-008 - Đếm số phiên khách đã tạo từ IP này
        stmt = select(func.count(ResearchSession.id)).where(
            ResearchSession.user_id.is_(None),
            ResearchSession.client_ip == client_ip
        )
        res = await db.execute(stmt)
        guest_session_count = res.scalar() or 0

        if guest_session_count >= settings.GUEST_MAX_SESSIONS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Chế độ khách đã dùng hết {settings.GUEST_MAX_SESSIONS} lượt nghiên cứu trải nghiệm miễn phí. Vui lòng đăng ký hoặc đăng nhập tài khoản để tiếp tục nghiên cứu không giới hạn."
            )

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
        client_ip=client_ip,
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

# @trace: REQ-001, REQ-002, REQ-009
@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    REQ-009: Lấy danh sách các phiên nghiên cứu với cơ chế phân lập bảo mật tuyệt đối:
    - Nếu đã đăng nhập: CHỈ trả về đúng các phiên do chính tài khoản đó tạo (user_id == current_user.id).
    - Nếu là khách (chưa đăng nhập): CHỈ trả về các phiên do chính IP của máy khách đó tạo (user_id is None and client_ip == client_ip). Tuyệt đối không hiển thị dữ liệu của người khác ra ngoài.
    """
    stmt = select(ResearchSession).order_by(desc(ResearchSession.created_at)).limit(limit).offset(offset)
    if current_user:
        stmt = stmt.where(ResearchSession.user_id == current_user.id)
    else:
        # Lấy IP của khách để chỉ lọc phiên của riêng khách đó
        forwarded = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = "127.0.0.1"

        stmt = stmt.where(
            ResearchSession.user_id.is_(None),
            ResearchSession.client_ip == client_ip
        )

    res = await db.execute(stmt)
    return res.scalars().all()

# @trace: REQ-001, REQ-002
@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Xem chi tiết thông tin của một phiên nghiên cứu:
    - Kiểm tra quyền truy cập (không xem nhầm dữ liệu của tài khoản khác).
    - Kèm theo số lượng bài báo (paper_count).
    - Lấy ID báo cáo mới nhất.
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

    verify_session_access(session, current_user)

    latest_report = session.reports[-1] if session.reports else None

    return SessionDetailResponse(
        id=session.id,
        user_id=session.user_id,
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

# @trace: REQ-001, REQ-002
@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    payload: SessionUpdate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Cập nhật chủ đề, câu hỏi nghiên cứu hoặc tham số của một phiên đang tồn tại.
    Chỉ cho phép chủ sở hữu phiên thực hiện.
    """
    stmt = select(ResearchSession).where(ResearchSession.id == session_id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    verify_session_access(session, current_user)

    if payload.topic is not None:
        session.topic = payload.topic
    if payload.research_question is not None:
        session.research_question = payload.research_question
    if payload.parameters is not None:
        session.parameters = payload.parameters

    await db.commit()
    await db.refresh(session)
    return session

# @trace: REQ-001, REQ-002
@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Xóa bỏ một phiên nghiên cứu và toàn bộ dữ liệu phụ thuộc liên quan (cascade).
    Chỉ cho phép chủ sở hữu phiên thực hiện.
    """
    stmt = select(ResearchSession).where(ResearchSession.id == session_id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    verify_session_access(session, current_user)

    await db.delete(session)
    await db.commit()
    return None

