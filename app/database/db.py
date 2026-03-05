import asyncio
from contextlib import asynccontextmanager

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from app.settings import Settings


settings = Settings()
engine: AsyncEngine | None = None
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None
Base = declarative_base()


async def init_engine() -> AsyncEngine:
    global engine, AsyncSessionLocal
    if engine is not None:
        return engine
    engine = create_engine(
        settings.database_url,
        future=True,
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    )
    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    await _create_tables()
    return engine


async def _create_tables() -> None:
    global Base
    async with engine.begin() as conn:  # type: ignore[union-attr]
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncSession:
    if AsyncSessionLocal is None:
        await init_engine()
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_engine() -> None:
    global engine
    if engine is not None:
        await engine.dispose()
        engine = None
        global AsyncSessionLocal
        AsyncSessionLocal = None


def create_tables_sync() -> None:
    from sqlalchemy import inspect

    sync_engine = create_engine(settings.database_url, future=True)
    inspector = inspect(sync_engine)
    if not inspector.has_table(Base.metadata.tables["tool"]):
        Base.metadata.create_all(bind=sync_engine)


async def main() -> None:
    await init_engine()
    async with get_session() as session:
        result = await session.execute(text("SELECT 1"))
        print(result.scalar())
    await close_engine()


if __name__ == "__main__":
    asyncio.run(main())