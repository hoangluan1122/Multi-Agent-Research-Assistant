"""
Module khởi tạo và cấu hình ứng dụng FastAPI chính của hệ thống PaperFlow.
Thiết lập vòng đời ứng dụng (lifespan), middleware CORS, router API v1, health check và phục vụ Frontend SPA tĩnh.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.db.session import init_db
from app.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Quản lý vòng đời (Lifespan) của FastAPI:
    - Khi khởi động (Startup): Cấu hình logging, khởi tạo bảng cơ sở dữ liệu SQLite/PostgreSQL.
    - Khi tắt (Shutdown): Giải phóng tài nguyên và ghi log kết thúc.
    """
    # Khởi động: Thiết lập logging và khởi tạo các bảng cơ sở dữ liệu
    setup_logging()
    logger.info("Initializing PaperFlow database tables...")
    await init_db()
    logger.info(f"{settings.PROJECT_NAME} v{settings.VERSION} started successfully.")
    yield
    # Khi ứng dụng dừng
    logger.info("Shutting down PaperFlow API...")

def create_application() -> FastAPI:
    """
    Hàm tạo và cấu hình ứng dụng FastAPI chính:
    - Đăng ký metadata cho tài liệu API Swagger/Redoc.
    - Cấu hình CORS middleware cho phép các nguồn truy cập (Frontend).
    - Đăng ký các API router v1.
    - Đăng ký endpoint kiểm tra trạng thái hoạt động (/api/health).
    - Mount thư mục tĩnh Frontend (dist) để chạy giao diện web trên cùng 1 cổng.
    """
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description="Backend API và Hệ thống Multi-Agent hỗ trợ nghiên cứu khoa học tự động (PaperFlow)",
        version=settings.VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Cấu hình CORS (Cross-Origin Resource Sharing)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Đăng ký tập hợp router API phiên bản v1
    application.include_router(api_router, prefix=settings.API_V1_STR)

    @application.get("/api/health", summary="Kiểm tra trạng thái hệ thống")
    async def health_check():
        """
        Endpoint kiểm tra trạng thái sức khỏe của Backend, nhà cung cấp LLM và bộ nhớ vector Qdrant.
        """
        return {
            "status": "healthy",
            "version": settings.VERSION,
            "llm_provider": settings.LLM_PROVIDER,
            "qdrant_memory": settings.QDRANT_USE_MEMORY
        }

    # Phục vụ Frontend SPA trên cùng cổng nếu đã build thư mục dist
    frontend_dist = Path(__file__).resolve().parents[2] / "Frontend" / "dist"
    if frontend_dist.exists() and (frontend_dist / "index.html").exists():
        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():
            # Mount thư mục assets tĩnh (JS, CSS, hình ảnh)
            application.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @application.get("/{full_path:path}", summary="Phục vụ trang giao diện SPA")
        async def serve_spa(full_path: str):
            """
            Hỗ trợ cơ chế định tuyến Single Page Application (SPA), trả về file hoặc index.html.
            """
            file_path = frontend_dist / full_path
            if full_path and file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(frontend_dist / "index.html")
    else:
        @application.get("/", summary="Trang chủ API (chế độ chỉ chạy Backend)")
        async def root():
            """
            Trả về thông tin cơ bản về API khi chưa có bản build của Frontend.
            """
            return {
                "name": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "status": "online",
                "docs": "/docs",
                "api_v1": settings.API_V1_STR,
            }

    return application

# Khởi tạo instance ứng dụng FastAPI
app = create_application()

