"""
Lớp Agent cơ sở (BaseAgent) cho toàn bộ các tác tử trong PaperFlow.
Tích hợp Google Agent Development Kit (ADK), quản lý vòng đời, ghi nhận nhật ký (AgentRun) và cơ chế xử lý lỗi nhất quán.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from google.adk.agents import Agent
from ..models.agent_run import AgentRun
from ..core.config import settings

logger = logging.getLogger("paperflow.agent")

class BaseAgent(ABC):
    """
    Lớp trừu tượng định nghĩa khung sườn chung cho tất cả các Agent:
    - Khởi tạo instance Google ADK Agent tương ứng.
    - Cung cấp phương thức ghi nhật ký log_start / log_end vào bảng agent_runs.
    - Định nghĩa hàm trừu tượng `run` bắt buộc mỗi Agent phải triển khai logic riêng.
    """
    def __init__(
        self,
        name: str,
        description: str,
        instruction: Optional[str] = None,
        model: Optional[str] = None,
        tools: Optional[List[Callable]] = None
    ):
        self.name = name
        self.description = description
        self.instruction = instruction or description
        self.model_name = model or settings.DEFAULT_LLM_MODEL
        self.tools = tools or []

        # Khởi tạo đối tượng Agent cốt lõi của Google ADK (Agent Development Kit)
        self.adk_agent = Agent(
            name=self.name,
            model=self.model_name,
            instruction=self.instruction,
            tools=self.tools
        )

    async def log_start(
        self,
        db: AsyncSession,
        session_id: str,
        step_description: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> AgentRun:
        """Ghi nhận thời điểm bắt đầu chạy của Agent vào Database (trạng thái RUNNING)."""
        run = AgentRun(
            session_id=session_id,
            agent_name=self.name,
            status="RUNNING",
            step_description=step_description,
            input_data=input_data or {},
            started_at=datetime.utcnow()
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)
        logger.info(f"[{self.name}] Started: {step_description} (Session: {session_id})")
        return run

    async def log_end(
        self,
        db: AsyncSession,
        run: AgentRun,
        status: str = "COMPLETED",
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ):
        """Cập nhật kết thúc quá trình chạy của Agent (COMPLETED hoặc FAILED) kèm dữ liệu đầu ra và thời gian kết thúc."""
        run.status = status
        run.output_data = output_data or {}
        run.error_message = error_message
        run.ended_at = datetime.utcnow()
        await db.commit()
        logger.info(f"[{self.name}] Finished with status: {status}")

    @abstractmethod
    async def run(self, db: AsyncSession, session_id: str, **kwargs) -> Dict[str, Any]:
        """Phương thức trừu tượng thực thi logic nghiệp vụ cốt lõi của từng Agent."""
        pass

