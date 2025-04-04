import secrets
from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.repositories.utils import decrypt_auth_data
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.mocks import (
    MockConnection,
    MockCredentials,
    MockGroup,
    MockUser,
    UserTestRoles,
)
from tests.test_unit.conftest import create_group_member
from tests.test_unit.utils import (
    create_connection,
    create_credentials,
    create_group,
    create_user,
)


@pytest_asyncio.fixture
async def group_connection(
    session: AsyncSession,
    settings: Settings,
    connection_type: str | None,
    create_connection_data: dict | None,
    create_connection_auth_data: dict | None,
    access_token_factory,
) -> AsyncGenerator[MockConnection, None]:
    group_owner = await create_user(
        session=session,
        username=f"{secrets.token_hex(5)}_group_connection_owner",
        is_active=True,
    )
    group = await create_group(
        session=session,
        name=f"{secrets.token_hex(5)}_group_for_group_connection",
        owner_id=group_owner.id,
    )
    members: list[MockUser] = []
    for username in (
        f"{secrets.token_hex(5)}_connection_group_member_maintainer",
        f"{secrets.token_hex(5)}_connection_group_member_developer",
        f"{secrets.token_hex(5)}_connection_group_member_guest",
    ):
        members.append(
            await create_group_member(
                username=username,
                group_id=group.id,
                session=session,
                access_token_factory=access_token_factory,
            ),
        )

    await session.commit()
    connection = await create_connection(
        session=session,
        name=f"{secrets.token_hex(5)}_group_for_group_connection",
        type=connection_type or "postgres",
        group_id=group.id,
        data=create_connection_data,
    )

    credentials = await create_credentials(
        session=session,
        settings=settings,
        connection_id=connection.id,
        auth_data=create_connection_auth_data,
    )
    token = access_token_factory(group_owner.id)
    yield MockConnection(
        credentials=MockCredentials(
            value=decrypt_auth_data(credentials.value, settings=settings),
            connection_id=connection.id,
        ),
        connection=connection,
        owner_group=MockGroup(
            group=group,
            owner=MockUser(
                user=group_owner,
                auth_token=token,
                role=UserTestRoles.Owner,
            ),
            members=members,
        ),
    )
    await session.delete(credentials)
    await session.delete(connection)
    await session.delete(group_owner)
    await session.delete(group)
    for member in members:
        await session.delete(member.user)
    await session.commit()
