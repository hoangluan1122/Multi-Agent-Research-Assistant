"""
Script khởi chạy chính của hệ thống PaperFlow.
Tự động build Frontend (nếu chưa build) và khởi chạy Backend FastAPI server.
"""

import os
import sys
import subprocess
from pathlib import Path

# Đường dẫn thư mục gốc và các thư mục thành phần
ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "Frontend"
BACKEND_DIR = ROOT_DIR / "Backend"
DIST_DIR = FRONTEND_DIR / "dist"
# Xác định đường dẫn Python trong môi trường ảo (.venv)
VENV_PYTHON = BACKEND_DIR / ".venv" / "Scripts" / "python.exe" if sys.platform == "win32" else BACKEND_DIR / ".venv" / "bin" / "python"

def build_frontend():
    """
    Build mã nguồn Frontend (React + Vite) thành thư mục tĩnh (dist).
    """
    print("📦 [PaperFlow] Đang build Frontend...")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    result = subprocess.run([npm_cmd, "run", "build"], cwd=FRONTEND_DIR)
    if result.returncode != 0:
        print("❌ Build Frontend thất bại.")
        sys.exit(1)
    print("✅ Build Frontend hoàn tất.")

def run_server():
    """
    Khởi động máy chủ ứng dụng:
    - Chuyển sang dùng Python môi trường ảo nếu đang chạy Python hệ thống.
    - Kiểm tra và tự động build frontend nếu chưa có thư mục dist hoặc có cờ --build.
    - Khởi chạy uvicorn server phục vụ cả API và static files.
    """
    # Nếu chạy bằng python ngoài .venv, tự động gọi lại bằng python trong .venv
    if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
        print(f"🔄 Sử dụng virtualenv: {VENV_PYTHON}")
        subprocess.run([str(VENV_PYTHON), str(Path(__file__).resolve())] + sys.argv[1:])
        return

    # Tự động build frontend nếu chưa có bản build dist hoặc truyền cờ --build
    if not (DIST_DIR / "index.html").exists() or "--build" in sys.argv:
        build_frontend()

    print("🚀 [PaperFlow] Đang khởi chạy ứng dụng (Backend + Frontend) tại http://localhost:8000")
    print("📖 Swagger Docs: http://localhost:8000/docs")
    
    # Thêm thư mục Backend vào sys.path để import các module của app
    sys.path.insert(0, str(BACKEND_DIR))
    import uvicorn
    from app.core.config import settings

    # Chạy uvicorn server
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        app_dir=str(BACKEND_DIR)
    )

if __name__ == "__main__":
    run_server()

