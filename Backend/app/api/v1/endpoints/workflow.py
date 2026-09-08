"""
Endpoint điều phối Workflow & Tác tử Multi-Agent (Workflow API - UC009, UC010, UC011).
Cung cấp API kích hoạt chu trình nghiên cứu tự động chạy nền (background task), theo dõi trạng thái và stream sự kiện SSE thời gian thực.
"""

import json
import asyncio
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.models.session import ResearchSession
from app.models.agent_run import AgentRun
from app.orchestrator.workflow import workflow_engine
from app.orchestrator.state import workflow_broadcaster
from app.schemas.agent import (
    WorkflowStartRequest,
    WorkflowStatusResponse,
    AgentRunResponse,
)

router = APIRouter(prefix="/workflow", tags=["Workflow & Agents (UC009, UC010, UC011)"])

@router.post("/start", status_code=status.HTTP_202_ACCEPTED)
async def start_research_workflow(
    payload: WorkflowStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Kích hoạt chu trình nghiên cứu Multi-Agent tự động cho một phiên:
    - Kiểm tra trạng thái phiên xem có đang chạy hay không.
    - Đẩy tác vụ chạy nền `workflow_engine.run_full_workflow` qua FastAPI BackgroundTasks.
    - Trả về phản hồi tức thì với mã HTTP 202 Accepted.
    """
    stmt = select(ResearchSession).where(ResearchSession.id == payload.session_id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    if session.status == "RUNNING":
        return {"message": "Workflow is already running for this session", "session_id": payload.session_id}

    params = session.parameters or {}
    citation_style = params.get("citation_style", "IEEE")

    # Chạy quy trình Multi-Agent bất đồng bộ dưới dạng tác vụ nền
    background_tasks.add_task(
        workflow_engine.run_full_workflow,
        session_id=payload.session_id,
        auto_search=payload.auto_search,
        max_papers=payload.max_papers,
        citation_style=citation_style
    )

    return {
        "message": "Multi-Agent workflow started successfully",
        "session_id": payload.session_id,
        "status": "RUNNING"
    }

@router.get("/status/{session_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Tra cứu trạng thái thực thi hiện tại của quy trình Multi-Agent:
    - Tính toán % tiến độ hoàn thành dựa trên chặng bước (`current_step`).
    - Trả về toàn bộ danh sách lịch sử chạy của các Agent (`agent_runs`).
    """
    stmt = select(ResearchSession).where(ResearchSession.id == session_id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    # Truy vấn danh sách lịch sử thực thi của các tác tử
    r_stmt = select(AgentRun).where(AgentRun.session_id == session_id).order_by(AgentRun.started_at)
    r_res = await db.execute(r_stmt)
    runs = r_res.scalars().all()

    # Bảng quy đổi tiến độ phần trăm tương ứng với từng bước
    progress_map = {
        "READY": 0,
        "QUEUED": 5,
        "STARTING_WORKFLOW": 10,
        "SEARCHING_PAPERS": 20,
        "READING_AND_EMBEDDING": 50,
        "SUMMARIZING_AND_COMPARING": 70,
        "FORMATTING_CITATIONS": 80,
        "WRITING_DRAFT": 88,
        "REVIEWING": 95,
        "COMPLETED": 100,
        "FAILED": 0
    }
    progress = progress_map.get(session.current_step, progress_map.get(session.status, 0))

    return WorkflowStatusResponse(
        session_id=session.id,
        status=session.status,
        current_step=session.current_step,
        current_agent=runs[-1].agent_name if (runs and session.status == "RUNNING") else None,
        progress_percentage=progress,
        message=session.current_step.replace("_", " ").title(),
        agent_runs=[AgentRunResponse.model_validate(r) for r in runs],
        error_message=session.error_message
    )

@router.get("/stream/{session_id}")
async def stream_workflow_progress(session_id: str):
    """
    Luồng Server-Sent Events (SSE) phát trực tiếp tiến trình theo thời gian thực tới giao diện React:
    - Duy trì kết nối liên tục, tự động gửi ping keep-alive mỗi 30s.
    - Đóng kết nối khi hoàn tất (COMPLETED) hoặc thất bại (FAILED).
    """
    queue = workflow_broadcaster.subscribe(session_id)

    async def event_generator():
        try:
            # Gửi thông điệp kết nối ban đầu
            yield f"data: {json.dumps({'type': 'CONNECTED', 'session_id': session_id})}\n\n"
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(data)}\n\n"
                    if data.get("status") in ["COMPLETED", "FAILED"]:
                        break
                except asyncio.TimeoutError:
                    # Gửi heartbeat giữ kết nối SSE không bị timeout bởi proxy
                    yield f": ping\n\n"
        finally:
            workflow_broadcaster.unsubscribe(session_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

