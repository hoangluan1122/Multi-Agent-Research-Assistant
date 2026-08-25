"""
Script khoi chay truc tiep may chu Uvicorn cho Backend PaperFlow.
Tu dong uu tien project venv va tao/check dependencies truoc khi chay app.
"""

import os
import subprocess
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
VENV_DIR = BACKEND_DIR / ".venv"
if os.name == "nt":
    VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
else:
    VENV_PYTHON = VENV_DIR / "bin" / "python"
REQUIREMENTS_FILE = BACKEND_DIR / "requirements.txt"
MIN_PYTHON = (3, 11)
MAX_PYTHON = (3, 13)
REQUIRED_IMPORTS = (
    "fastapi",
    "uvicorn",
    "pydantic_settings",
    "sqlalchemy",
    "httpx",
    "pypdf",
    "docx",
    "reportlab",
    "qdrant_client",
    "google.generativeai",
    "openai",
    "numpy",
)


def ensure_supported_python() -> None:
    """Dung som neu Python version khong phu hop voi dependency da pin."""
    if MIN_PYTHON <= sys.version_info[:2] < MAX_PYTHON:
        return

    min_version = ".".join(str(part) for part in MIN_PYTHON)
    max_version = ".".join(str(part) for part in MAX_PYTHON)
    current_version = ".".join(str(part) for part in sys.version_info[:3])
    print(
        "[run.py] Python "
        f"{current_version} khong duoc ho tro. Project nay can Python >= {min_version} va < {max_version} "
        "vi mot so dependency backend chua cai on dinh tren Python 3.14. "
        "Hay cai Python 3.11/3.12, xoa Backend\\.venv, roi chay lai `python Backend\\run.py`.",
        file=sys.stderr,
    )
    raise SystemExit(1)


def running_in_project_venv() -> bool:
    """Kiem tra script co dang chay bang Python trong project venv khong."""
    return VENV_PYTHON.exists() and Path(sys.executable).resolve() == VENV_PYTHON.resolve()


def ensure_project_python() -> None:
    """Tao venv neu can va chay lai script bang Python cua project venv."""
    if not VENV_PYTHON.exists():
        ensure_supported_python()
        print(f"[run.py] Tao moi truong ao tai: {VENV_DIR}")
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)

    if not VENV_PYTHON.exists():
        raise FileNotFoundError(f"Khong tim thay Python trong venv: {VENV_PYTHON}")

    if not running_in_project_venv():
        print(f"[run.py] Dung interpreter du an: {VENV_PYTHON}", flush=True)
        result = subprocess.run([str(VENV_PYTHON), str(Path(__file__).resolve())] + sys.argv[1:], check=False)
        raise SystemExit(result.returncode)

    ensure_supported_python()


def ensure_env() -> None:
    """Dam bao requirements backend da duoc cai dat trong project venv."""
    if not REQUIREMENTS_FILE.exists():
        raise FileNotFoundError(f"Khong tim thay file requirements: {REQUIREMENTS_FILE}")

    missing_modules = []
    for module_name in REQUIRED_IMPORTS:
        try:
            __import__(module_name)
        except ModuleNotFoundError:
            missing_modules.append(module_name)

    if missing_modules:
        print(f"[run.py] Thieu dependencies: {', '.join(missing_modules)}")
        print("[run.py] Cai dat dependencies backend...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)], check=True)


if __name__ == "__main__":
    ensure_project_python()
    ensure_env()

    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))

    os.chdir(BACKEND_DIR)

    try:
        import uvicorn
    except ModuleNotFoundError:
        print("[run.py] Missing dependencies, installing from requirements.txt...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)], check=True)
        import uvicorn

    from app.core.config import settings

    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level="info",
        app_dir=str(BACKEND_DIR),
    )
