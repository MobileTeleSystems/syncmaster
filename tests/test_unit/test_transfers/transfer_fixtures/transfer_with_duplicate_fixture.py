import secrets

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Queue
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.mocks import MockTransfer
from tests.test_unit.utils import create_connection, create_credentials, create_transfer


@pytest_asyncio.fixture
async def group_transfer_with_same_name(
    session: AsyncSession,
    settings: Settings,
    group_queue: Queue,
    group_transfer: MockTransfer,
) -> None:
    source_connection = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        group_id=group_queue.group_id,
    )
    await create_credentials(
        session=session,
        settings=settings,
        connection_id=source_connection.id,
    )
    target_connection = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        group_id=group_queue.group_id,
    )
    await create_credentials(
        session=session,
        settings=settings,
        connection_id=target_connection.id,
    )

    transfer = await create_transfer(
        session=session,
        name="duplicated_group_transfer",
        group_id=group_queue.group_id,
        source_connection_id=source_connection.id,
        target_connection_id=target_connection.id,
        queue_id=group_queue.id,
    )

    yield
    await session.delete(source_connection)
    await session.delete(target_connection)
    await session.delete(transfer)
    await session.commit()
