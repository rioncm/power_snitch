from __future__ import annotations

from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from powersnitch_app.config import Settings


def sqlite_url_from_path(path: str) -> str:
    return f"sqlite+aiosqlite:///{path}"


class Database:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.url = sqlite_url_from_path(str(self.settings.sqlite_path))
        self.engine: AsyncEngine = create_async_engine(self.url, future=True)
        self.session_factory = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    @asynccontextmanager
    async def session(self):
        async with self.session_factory() as session:
            yield session

