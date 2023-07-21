from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Group, User


@asynccontextmanager
async def create_user_cm(
    session: AsyncSession,
    username: str,
    is_active: bool = False,
    is_superuser: bool = False,
    is_deleted: bool = False,
) -> User:
    u = User(
        username=username,
        is_active=is_active,
        is_superuser=is_superuser,
        is_deleted=is_deleted,
    )
    session.add(u)
    await session.commit()
    await session.refresh(u)
    yield u
    await session.delete(u)
    await session.commit()


async def create_user(
    session: AsyncSession,
    username: str,
    is_active: bool = False,
    is_superuser: bool = False,
    is_deleted: bool = False,
) -> User:
    u = User(
        username=username,
        is_active=is_active,
        is_superuser=is_superuser,
        is_deleted=is_deleted,
    )
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return u


async def create_group(session: AsyncSession, name: str, admin_id: int) -> Group:
    g = Group(name=name, admin_id=admin_id)
    session.add(g)
    await session.commit()
    await session.refresh(g)
    return g
