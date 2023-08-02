from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Acl, Connection, Group, ObjectType, Rule, User


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


async def create_connection(
    session: AsyncSession,
    name: str,
    user_id: int | None,
    group_id: int | None,
    description: str = "",
    type: str = "postgres",
    host: str = "127.0.0.1",
    port: int = 5432,
    user: str = "user",
    password: str = "password",
    database_name: str | None = "db",
    additional_params: dict[str, Any] = {},
) -> Connection:
    c = Connection(
        user_id=user_id,
        group_id=group_id,
        name=name,
        description=description,
        data=dict(
            type=type,
            host=host,
            port=port,
            user=user,
            password=password,
            database_name=database_name,
            additional_params=additional_params,
        ),
    )
    session.add(c)
    await session.commit()
    await session.refresh(c)
    return c


async def create_acl(
    session: AsyncSession,
    object_id: int,
    object_type: ObjectType,
    user_id: int,
    rule: Rule,
):
    acl = Acl(
        object_id=object_id,
        object_type=object_type,
        user_id=user_id,
        rule=rule,
    )
    session.add(acl)
    await session.commit()
    await session.refresh(acl)
    return acl
