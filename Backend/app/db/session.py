"""
Module quản lý kết nối và phiên làm việc (Session) bất đồng bộ với Cơ sở dữ liệu.
Sử dụng SQLAlchemy AsyncEngine và AsyncSession.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.db.base import Base

# Khởi tạo Async Engine kết nối cơ sở dữ liệu (hỗ trợ cả PostgreSQL asyncpg và SQLite aiosqlite)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Factory tạo phiên làm việc cơ sở dữ liệu bất đồng bộ (AsyncSession)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def init_db():
    """
    Khởi tạo cấu trúc bảng trong cơ sở dữ liệu nếu chưa tồn tại.
    Import toàn bộ models để Base.metadata thu thập đầy đủ schema trước khi create_all.
    Tự động fallback sang SQLite nếu cơ sở dữ liệu PostgreSQL không khả dụng.
    """
    global engine, AsyncSessionLocal
    # Import tất cả các model để đảm bảo đã đăng ký trong Base.metadata
    import app.models  # noqa: F401
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        if "postgresql" in settings.DATABASE_URL:
            import logging
            logger = logging.getLogger("paperflow.db")
            logger.warning(f"Không thể kết nối PostgreSQL ({e}). Tự động chuyển sang SQLite cục bộ (paperflow.db)...")
            fallback_url = "sqlite+aiosqlite:///./paperflow.db"
            engine = create_async_engine(
                fallback_url,
                echo=False,
                future=True,
                connect_args={"check_same_thread": False}
            )
            AsyncSessionLocal = async_sessionmaker(
                bind=engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        else:
            raise

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency Injection cung cấp database session cho các FastAPI endpoint.
    Tự động commit khi xử lý thành công, rollback nếu gặp ngoại lệ và đóng session khi kết thúc.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

