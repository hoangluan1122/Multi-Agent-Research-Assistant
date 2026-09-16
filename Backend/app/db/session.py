"""
Module quản lý kết nối và phiên làm việc (Session) bất đồng bộ với Cơ sở dữ liệu.
Sử dụng SQLAlchemy AsyncEngine và AsyncSession.
"""

from typing import AsyncGenerator
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.db.base import Base


def normalize_database_url(database_url: str) -> URL:
    """Convert PostgreSQL URL options to arguments supported by asyncpg."""
    url = make_url(database_url)
    if url.drivername != "postgresql+asyncpg":
        return url

    query = dict(url.query)
    ssl_mode = query.pop("sslmode", None)
    query.pop("channel_binding", None)
    if ssl_mode and "ssl" not in query:
        query["ssl"] = ssl_mode

    return url.set(query=query)


is_sqlite = "sqlite" in settings.DATABASE_URL
engine = create_async_engine(
    normalize_database_url(settings.DATABASE_URL),
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=60 if not is_sqlite else -1,
    connect_args={"check_same_thread": False} if is_sqlite else {}
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
    
    # @trace: REQ-007
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # @trace: REQ-007, REQ-008
        async with engine.begin() as conn:
            from sqlalchemy import text
            try:
                if "postgresql" in settings.DATABASE_URL:
                    await conn.execute(text("ALTER TABLE research_sessions ADD COLUMN IF NOT EXISTS client_ip VARCHAR(45)"))
                    await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_sessions_client_ip ON research_sessions (client_ip)"))
                elif "sqlite" in settings.DATABASE_URL:
                    try:
                        await conn.execute(text("ALTER TABLE research_sessions ADD COLUMN client_ip VARCHAR(45)"))
                    except Exception:
                        pass
                    try:
                        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_sessions_client_ip ON research_sessions (client_ip)"))
                    except Exception:
                        pass
                    try:
                        await conn.execute(text("ALTER TABLE research_sessions ADD COLUMN user_id VARCHAR(36)"))
                    except Exception:
                        pass
                    try:
                        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_sessions_user_id ON research_sessions (user_id)"))
                    except Exception:
                        pass
                    try:
                        await conn.execute(text("DELETE FROM reports WHERE id NOT IN (SELECT MIN(id) FROM reports GROUP BY session_id, version)"))
                        await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_session_report_version ON reports (session_id, version)"))
                    except Exception:
                        pass
            except Exception:
                pass
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
                from sqlalchemy import text
                try:
                    await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_session_report_version ON reports (session_id, version)"))
                except Exception:
                    pass
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

