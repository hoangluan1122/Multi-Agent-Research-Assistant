"""
Module quản lý trạng thái luồng làm việc (WorkflowState) và phát sự kiện thời gian thực (Server-Sent Events - SSE).
Cho phép giao diện Frontend đăng ký nhận luồng thông tin tiến trình thực thi của các tác tử Multi-Agent.
"""

import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator
from pydantic import BaseModel, Field

class WorkflowState(BaseModel):
    """Lớp cấu trúc dữ liệu mô tả trạng thái chi tiết của quy trình Multi-Agent tại một thời điểm."""
    session_id: str
    status: str = "READY"  # Các trạng thái: READY, QUEUED, RUNNING, REVIEWING, COMPLETED, FAILED
    current_step: str = "INITIALIZED"
    current_agent: Optional[str] = None
    progress: int = 0
    message: str = "Ready to start"
    error: Optional[str] = None
    report_id: Optional[str] = None

class WorkflowEventBroadcaster:
    """
    Bộ quản lý và phân phối sự kiện Server-Sent Events (SSE) theo phiên nghiên cứu:
    - Cho phép nhiều kết nối Client (Browser Tabs) cùng lắng nghe một phiên.
    - Phát tin nhắn (broadcast) bất đồng bộ tới toàn bộ hàng đợi asyncio.Queue đang hoạt động.
    """
    def __init__(self):
        # Dictionary lưu danh sách Queue theo từng session_id: {session_id: [Queue, Queue, ...]}
        self._listeners: Dict[str, List[asyncio.Queue]] = {}

    def subscribe(self, session_id: str) -> asyncio.Queue:
        """Đăng ký hàng đợi nhận sự kiện SSE mới cho một session_id cụ thể."""
        if session_id not in self._listeners:
            self._listeners[session_id] = []
        q = asyncio.Queue()
        self._listeners[session_id].append(q)
        return q

    def unsubscribe(self, session_id: str, q: asyncio.Queue):
        """Hủy đăng ký hàng đợi khi client ngắt kết nối hoặc đóng tab."""
        if session_id in self._listeners:
            if q in self._listeners[session_id]:
                self._listeners[session_id].remove(q)
            if not self._listeners[session_id]:
                del self._listeners[session_id]

    async def broadcast(self, session_id: str, data: Dict[str, Any]):
        """Gửi gói dữ liệu sự kiện tới tất cả các client đang theo dõi phiên nghiên cứu này."""
        if session_id in self._listeners:
            for q in list(self._listeners[session_id]):
                try:
                    await q.put(data)
                except Exception:
                    pass

# Khởi tạo singleton instance cho bộ phát sự kiện
workflow_broadcaster = WorkflowEventBroadcaster()

