"""
Điểm vào (Entry point) cho ASGI server (Uvicorn / Gunicorn).
Export đối tượng ứng dụng FastAPI từ app.main.
"""

from app.main import app

__all__ = ["app"]

