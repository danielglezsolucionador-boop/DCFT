from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.core.config import settings


settings.state_dir.mkdir(parents=True, exist_ok=True)


def create_engine() -> AsyncEngine:
    kwargs = {
        "pool_pre_ping": True,
        "future": True,
        "connect_args": settings.database_connect_args,
    }
    if settings.database_backend == "postgresql":
        kwargs.update(
            {
                "pool_size": settings.database_pool_size,
                "max_overflow": settings.database_max_overflow,
                "pool_timeout": settings.database_pool_timeout,
            }
        )
    return create_async_engine(settings.effective_database_url, **kwargs)


engine = create_engine()
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def dispose_engine() -> None:
    await engine.dispose()


async def database_status() -> dict:
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("select 1"))
            result.scalar_one()
        return {"status": "ok", "backend": settings.database_backend, "reason": "connection_ok"}
    except Exception as exc:
        return {"status": "unavailable", "backend": settings.database_backend, "reason": exc.__class__.__name__}
