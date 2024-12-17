from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from onetl.connection import FileConnection
from onetl.impl import LocalPath, RemotePath
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from syncmaster.backend.settings import ServerAppSettings as Settings
from syncmaster.db.models import (
    AuthData,
    Connection,
    Group,
    Queue,
    Run,
    Status,
    Transfer,
    User,
)
from syncmaster.db.repositories.utils import encrypt_auth_data
from syncmaster.schemas.v1.transfers import ReadFullTransferSchema


@asynccontextmanager
async def create_user_cm(
    session: AsyncSession,
    username: str,
    is_active: bool = False,
    is_superuser: bool = False,
    is_deleted: bool = False,
    email: str = None,
    first_name: str = None,
    middle_name: str = None,
    last_name: str = None,
) -> AsyncGenerator[User, None]:
    email = email or f"{username}@user.user"
    first_name = first_name or f"{username}_first"
    middle_name = middle_name or f"{username}_middle"
    last_name = last_name or f"{username}_last"
    u = User(
        username=username,
        email=email,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
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
    email: str = None,
    first_name: str = None,
    middle_name: str = None,
    last_name: str = None,
) -> User:
    email = email or f"{username}@user.user"
    first_name = first_name or f"{username}_first"
    middle_name = middle_name or f"{username}_middle"
    last_name = last_name or f"{username}_last"
    u = User(
        username=username,
        email=email,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        is_active=is_active,
        is_superuser=is_superuser,
        is_deleted=is_deleted,
    )
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return u


async def create_queue(
    session: AsyncSession,
    name: str,
    group_id: int,
    slug: str | None = None,
    description: str | None = None,
) -> Queue:
    queue = Queue(
        name=name,
        description=description,
        group_id=group_id,
        slug=slug if slug is not None else f"{group_id}-{name}",
    )
    session.add(queue)
    await session.commit()
    await session.refresh(queue)
    return queue


async def create_group(session: AsyncSession, name: str, owner_id: int) -> Group:
    g = Group(name=name, owner_id=owner_id)
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
            "type": "basic",
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
    type: str = "postgres",
    group_id: int | None = None,
    description: str = "",
    data: dict[str, Any] | None = None,
) -> Connection:
    if data is None:
        data = {
            "host": "127.0.0.1",
            "port": 5432,
            "database_name": "db",
            "additional_params": {},
        }

    c = Connection(
        group_id=group_id,
        name=name,
        description=description,
        type=type,
        data=data,
    )
    session.add(c)
    await session.commit()
    await session.refresh(c)
    return c


async def create_transfer(
    session: AsyncSession,
    name: str,
    source_connection_id: int,
    target_connection_id: int,
    queue_id: int,
    group_id: int | None = None,
    source_params: dict | None = None,
    target_params: dict | None = None,
    is_scheduled: bool = True,
    schedule: str = "* * * * *",
    strategy_params: dict | None = None,
    description: str = "",
) -> Transfer:
    t = Transfer(
        name=name,
        description=description,
        group_id=group_id,
        source_connection_id=source_connection_id,
        source_params=source_params or {"type": "postgres", "table_name": "table1"},
        target_connection_id=target_connection_id,
        target_params=target_params or {"type": "postgres", "table_name": "table1"},
        is_scheduled=is_scheduled,
        schedule=schedule,
        strategy_params=strategy_params or {"type": "full"},
        queue_id=queue_id,
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


def upload_files(
    source_path: os.PathLike | str,
    remote_path: os.PathLike | str,
    file_connection: FileConnection,
) -> list[RemotePath]:
    remote_files = []

    local_path = LocalPath(source_path)

    if local_path.exists() and local_path.is_dir():
        for root_path, _dir_names, file_names in os.walk(local_path):
            local_root = LocalPath(root_path)
            remote_root = RemotePath(remote_path) / local_root.relative_to(local_path)

            for filename in file_names:
                local_filename = local_root / filename
                remote_filename = remote_root / filename
                file_connection.upload_file(local_filename, remote_filename)
                remote_files.append(remote_filename)

    if not remote_files:
        raise RuntimeError(
            f"Could not load file examples from {local_path}. Path should exist and should contain samples",
        )

    return remote_files
