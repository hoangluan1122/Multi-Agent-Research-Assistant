"""
Router tổng hợp cho API v1:
Gộp toàn bộ các router con (sessions, papers, workflow, reports, config) thành một router tập trung.
"""

from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.sessions import router as sessions_router
from app.api.v1.endpoints.papers import router as papers_router
from app.api.v1.endpoints.workflow import router as workflow_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.config import router as config_router

# Router chính của API v1
api_router = APIRouter()

# Tích hợp các router endpoint chức năng
api_router.include_router(auth_router)
api_router.include_router(sessions_router)
api_router.include_router(papers_router)
api_router.include_router(workflow_router)
api_router.include_router(reports_router)
api_router.include_router(config_router)

