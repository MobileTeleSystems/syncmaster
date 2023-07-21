from collections.abc import AsyncGenerator, Callable
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.provider import DatabaseProvider


def create_engine(connection_uri: str, **engine_kwargs: Any) -> AsyncEngine:
    return create_async_engine(url=connection_uri, **engine_kwargs)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


def create_holder(
    session_factory: async_sessionmaker[AsyncSession],
) -> Callable[[], AsyncGenerator[DatabaseProvider, None]]:
    async def wrapper():
        async with session_factory() as session:
            yield DatabaseProvider(session=session)

    return wrapper
