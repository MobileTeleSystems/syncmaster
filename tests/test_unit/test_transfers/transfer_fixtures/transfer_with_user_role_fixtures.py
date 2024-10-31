import secrets

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Connection, Queue
from syncmaster.settings import Settings
from tests.mocks import MockTransfer, UserTestRoles
from tests.test_unit.conftest import add_user_to_group
from tests.test_unit.utils import create_connection, create_credentials, create_transfer


@pytest_asyncio.fixture
async def group_transfer_and_group_maintainer_plus(
    session: AsyncSession,
    group_queue: Queue,
    group_transfer: MockTransfer,
    role_maintainer_plus: UserTestRoles,
    role_maintainer_or_below_without_guest: UserTestRoles,
) -> str:
    user = group_transfer.owner_group.get_member_of_role(role_maintainer_plus)

    await add_user_to_group(
        user=user.user,
        group_id=group_queue.group_id,
        session=session,
        role=role_maintainer_or_below_without_guest,
    )

    return role_maintainer_plus


@pytest_asyncio.fixture
async def group_transfer_with_same_name_maintainer_plus(
    session: AsyncSession,
    settings: Settings,
    group_queue: Queue,
    group_transfer: MockTransfer,
    role_maintainer_plus: UserTestRoles,
    role_maintainer_or_below_without_guest: UserTestRoles,
) -> str:
    user = group_transfer.owner_group.get_member_of_role(role_maintainer_plus)

    await add_user_to_group(
        user=user.user,
        group_id=group_queue.group_id,
        session=session,
        role=role_maintainer_or_below_without_guest,
    )

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

    yield role_maintainer_plus
    await session.delete(source_connection)
    await session.delete(target_connection)
    await session.delete(transfer)
    await session.commit()


@pytest_asyncio.fixture
async def group_transfer_and_group_developer_plus(
    session: AsyncSession,
    group_queue: Queue,
    group_transfer: MockTransfer,
    role_developer_plus: UserTestRoles,
    role_maintainer_or_below_without_guest: UserTestRoles,
) -> str:
    user = group_transfer.owner_group.get_member_of_role(role_developer_plus)

    await add_user_to_group(
        user=user.user,
        group_id=group_queue.group_id,
        session=session,
        role=role_maintainer_or_below_without_guest,
    )

    return role_developer_plus


@pytest_asyncio.fixture
async def group_transfer_and_group_connection_developer_plus(
    session: AsyncSession,
    group_queue: Queue,
    group_transfer: MockTransfer,
    role_developer_plus: UserTestRoles,
    role_maintainer_or_below_without_guest: UserTestRoles,
    settings: Settings,
) -> tuple[str, Connection]:
    user = group_transfer.owner_group.get_member_of_role(role_developer_plus)

    await add_user_to_group(
        user=user.user,
        group_id=group_queue.group_id,
        session=session,
        role=role_maintainer_or_below_without_guest,
    )

    connection = await create_connection(
        session=session,
        name="group_transfer_source_connection",
        group_id=group_queue.group_id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=connection.id,
    )

    yield role_developer_plus, connection
    await session.delete(connection)
    await session.commit()


@pytest_asyncio.fixture
async def group_transfer_and_group_developer_or_below(
    session: AsyncSession,
    group_queue: Queue,
    group_transfer: MockTransfer,
    role_developer_or_below: UserTestRoles,
    role_maintainer_or_below_without_guest: UserTestRoles,
) -> str:
    user = group_transfer.owner_group.get_member_of_role(role_developer_or_below)

    await add_user_to_group(
        user=user.user,
        group_id=group_queue.group_id,
        session=session,
        role=role_maintainer_or_below_without_guest,
    )

    return role_developer_or_below
