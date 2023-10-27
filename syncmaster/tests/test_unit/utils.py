from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.v1.transfers.schemas import ReadFullTransferSchema
from app.config import Settings
from app.db.models import (
    Acl,
    AuthData,
    Connection,
    Group,
    ObjectType,
    Rule,
    Run,
    Status,
    Transfer,
    User,
)
from app.db.repositories.utilites import encrypt_auth_data


@asynccontextmanager
async def create_user_cm(
    session: AsyncSession,
    username: str,
    is_active: bool = False,
    is_superuser: bool = False,
    is_deleted: bool = False,
) -> AsyncGenerator[User, None]:
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


async def create_credentials(
    session: AsyncSession,
    settings: Settings,
    connection_id: int,
    auth_data: dict[str, Any] | None = None,
) -> AuthData:
    if auth_data is None:
        auth_data = {
            "type": "postgres",
            "user": "user",
            "password": "password",
        }

    ad = AuthData(
        connection_id=connection_id,
        value=encrypt_auth_data(auth_data, settings=settings),
    )

    session.add(ad)
    await session.commit()
    await session.refresh(ad)
    return ad


async def create_connection(
    session: AsyncSession,
    name: str,
    user_id: int | None = None,
    group_id: int | None = None,
    description: str = "",
    data: dict[str, Any] | None = None,
) -> Connection:
    if data is None:
        data = {
            "type": "postgres",
            "host": "127.0.0.1",
            "port": 5432,
            "database_name": "db",
            "additional_params": {},
        }

    c = Connection(
        user_id=user_id,
        group_id=group_id,
        name=name,
        description=description,
        data=data,
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


async def create_transfer(
    session: AsyncSession,
    name: str,
    source_connection_id: int,
    target_connection_id: int,
    group_id: int | None = None,
    user_id: int | None = None,
    source_params: dict | None = None,
    target_params: dict | None = None,
    is_scheduled: bool = True,
    schedule: str = "0 0 * * *",
    strategy_params: dict | None = None,
    description: str = "",
) -> Transfer:
    t = Transfer(
        name=name,
        description=description,
        user_id=user_id,
        group_id=group_id,
        source_connection_id=source_connection_id,
        source_params=source_params or {"type": "postgres", "table_name": "table1"},
        target_connection_id=target_connection_id,
        target_params=target_params or {"type": "postgres", "table_name": "table1"},
        is_scheduled=is_scheduled,
        schedule=schedule,
        strategy_params=strategy_params or {"type": "full"},
    )
    session.add(t)
    await session.commit()
    await session.refresh(t)
    return t


async def create_run(
    session: AsyncSession,
    transfer_id: int,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    status: Status = Status.CREATED,
) -> Run:
    transfer = await session.get(
        Transfer,
        transfer_id,
        options=(
            joinedload(Transfer.source_connection),
            joinedload(Transfer.target_connection),
        ),
    )
    dump = ReadFullTransferSchema.from_orm(transfer).dict()
    r = Run(
        transfer_id=transfer_id,
        started_at=started_at,
        ended_at=ended_at,
        status=status,
        transfer_dump=dump,
    )
    session.add(r)
    await session.commit()
    await session.refresh(r)
    return r
