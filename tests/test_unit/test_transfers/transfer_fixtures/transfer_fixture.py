import secrets
from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.backend.api.v1.auth.utils import sign_jwt
from syncmaster.config import Settings
from syncmaster.db.repositories.utils import decrypt_auth_data
from tests.mocks import (
    MockConnection,
    MockCredentials,
    MockGroup,
    MockTransfer,
    MockUser,
    UserTestRoles,
)
from tests.test_unit.conftest import create_group_member
from tests.test_unit.utils import (
    create_connection,
    create_credentials,
    create_group,
    create_queue,
    create_transfer,
    create_user,
)


@pytest_asyncio.fixture
async def group_transfer(
    session: AsyncSession,
    settings: Settings,
    create_connection_data: dict | None,
    create_transfer_data: dict | None,
) -> AsyncGenerator[MockTransfer, None]:
    group_owner = await create_user(
        session=session,
        username="group_transfer_owner",
        is_active=True,
    )
    group = await create_group(
        session=session,
        name="group_for_group_transfer",
        owner_id=group_owner.id,
    )

    queue = await create_queue(
        session=session,
        name=f"{secrets.token_hex(5)}_test_queue",
        group_id=group.id,
    )

    members: list[MockUser] = []
    for username in (
        "transfer_group_member_maintainer",
        "transfer_group_member_developer",
        "transfer_group_member_guest",
    ):
        members.append(
            await create_group_member(
                username=username,
                group_id=group.id,
                session=session,
                settings=settings,
            ),
        )

    await session.commit()
    mock_group = MockGroup(
        group=group,
        owner=MockUser(
            user=group_owner,
            auth_token=sign_jwt(group_owner.id, settings),
            role=UserTestRoles.Owner,
        ),
        members=members,
    )

    source_connection = await create_connection(
        session=session,
        name="group_transfer_source_connection",
        group_id=group.id,
        data=create_connection_data,
    )
    source_connection_creds = await create_credentials(
        session=session,
        settings=settings,
        connection_id=source_connection.id,
    )
    target_connection = await create_connection(
        session=session,
        name="group_transfer_target_connection",
        group_id=group.id,
        data=create_connection_data,
    )
    target_connection_creds = await create_credentials(
        session=session,
        settings=settings,
        connection_id=target_connection.id,
    )

    transfer = await create_transfer(
        session=session,
        name="group_transfer",
        group_id=group.id,
        source_connection_id=source_connection.id,
        target_connection_id=target_connection.id,
        queue_id=queue.id,
        source_params=create_transfer_data,
        target_params=create_transfer_data,
    )

    yield MockTransfer(
        transfer=transfer,
        source_connection=MockConnection(
            connection=source_connection,
            owner_group=mock_group,
            credentials=MockCredentials(
                value=decrypt_auth_data(source_connection_creds.value, settings=settings),
                connection_id=source_connection.id,
            ),
        ),
        target_connection=MockConnection(
            connection=target_connection,
            owner_group=mock_group,
            credentials=MockCredentials(
                value=decrypt_auth_data(target_connection_creds.value, settings=settings),
                connection_id=target_connection.id,
            ),
        ),
        owner_group=mock_group,
    )
    await session.delete(transfer)
    await session.delete(source_connection)
    await session.delete(target_connection)
    await session.delete(group)
    await session.delete(group_owner)
    await session.delete(queue)
    for member in members:
        await session.delete(member.user)
    await session.commit()
