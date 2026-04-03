import ssl
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

_ssl_ctx = ssl.create_default_context()
if settings.environment != "production":
    # Supabase uses self-signed certs in some regions; skip verification in dev/staging.
    # In production, set ENVIRONMENT=production and ensure the host cert is trusted.
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = ssl.CERT_NONE

_connect_args: dict = {"ssl": _ssl_ctx}
if settings.environment == "production":
    # Supabase pooler (PgBouncer) doesn't support prepared statements
    _connect_args["statement_cache_size"] = 0

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args=_connect_args,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
