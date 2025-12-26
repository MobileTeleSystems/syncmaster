import secrets
from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Queue, User, UserGroup
from syncmaster.db.repositories.utils import decrypt_auth_data
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.mocks import (
    MockConnection,
    MockCredentials,
    MockGroup,
    MockUser,
    UserTestRoles,
)
from tests.test_unit.utils import (
    create_connection,
    create_credentials,
    create_group,
    create_queue,
    create_user,
)


async def create_group_member(
    username: str,
    group_id: int,
    session: AsyncSession,
    access_token_factory,
) -> MockUser:
    role_name = username.split("_")[-1]

    if role_name == "maintainer":
        role = UserTestRoles.Maintainer
    elif role_name == "developer":
        role = UserTestRoles.Developer
    elif role_name == "guest":
        role = UserTestRoles.Guest
    else:
        raise ValueError(f"Unknown role {role_name}.")

    user = await create_user(
        session,
        username,
        is_active=True,
    )

    session.add(
        UserGroup(
            group_id=group_id,
            user_id=user.id,
            role=role,
        ),
    )

    token = access_token_factory(user.id)
    return MockUser(
        user=user,
        auth_token=token,
        role=role,
    )


async def add_user_to_group(
    user: User,
    group_id: int,
    session: AsyncSession,
    role: str,
):
    session.add(
        UserGroup(
            group_id=group_id,
            user_id=user.id,
            role=role,
        ),
    )
    await session.commit()


@pytest_asyncio.fixture
async def empty_group(session: AsyncSession, access_token_factory) -> AsyncGenerator[MockGroup, None]:
    owner = await create_user(
        session=session,
        username="empty_group_owner",
        is_active=True,
    )
    group = await create_group(
        session=session,
        name="empty_group",
        owner_id=owner.id,
    )
    token = access_token_factory(owner.id)
    yield MockGroup(
        group=group,
        owner=MockUser(
            user=owner,
            auth_token=token,
            role=UserTestRoles.Owner,
        ),
        members=[],
    )
    await session.delete(group)
    await session.delete(owner)
    await session.commit()


@pytest_asyncio.fixture
async def group(session: AsyncSession, access_token_factory) -> AsyncGenerator[MockGroup, None]:
    owner = await create_user(
        session=session,
        username="notempty_group_owner",
        is_active=True,
    )
    group = await create_group(session=session, name="notempty_group", owner_id=owner.id)

    members: list[MockUser] = []
    for username in (
        "not_empty_group_member_maintainer",
        "not_empty_group_member_developer",
        "not_empty_group_member_guest",
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
    token = access_token_factory(owner.id)
    yield MockGroup(
        group=group,
        owner=MockUser(
            user=owner,
            auth_token=token,
            role=UserTestRoles.Owner,
        ),
        members=members,
    )
    await session.delete(group)
    await session.delete(owner)
    for member in members:
        await session.delete(member.user)
    await session.commit()


@pytest_asyncio.fixture
async def mock_group(
    session: AsyncSession,
    access_token_factory,
) -> AsyncGenerator[MockGroup, None]:
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

    yield MockGroup(
        group=group,
        owner=MockUser(
            user=group_owner,
            auth_token=access_token_factory(group_owner.id),
            role=UserTestRoles.Owner,
        ),
        members=members,
    )
    await session.delete(group_owner)
    await session.delete(group)
    for member in members:
        await session.delete(member.user)
    await session.commit()


@pytest_asyncio.fixture
async def group_queue(
    session: AsyncSession,
    mock_group: MockGroup,
) -> AsyncGenerator[Queue, None]:
    queue = await create_queue(
        session=session,
        name=f"{secrets.token_hex(5)}_test_queue",
        group_id=mock_group.id,
    )

    yield queue

    await session.delete(queue)
    await session.commit()


@pytest_asyncio.fixture
async def mock_queue(
    session: AsyncSession,
    group: MockGroup,
) -> AsyncGenerator[Queue, None]:
    queue = await create_queue(
        session=session,
        name=f"{secrets.token_hex(5)}_test_queue",
        group_id=group.group.id,
    )

    yield queue

    await session.delete(queue)
    await session.commit()


@pytest_asyncio.fixture
async def create_connection_data(request) -> dict | None:
    if hasattr(request, "param"):
        return request.param
    return None


@pytest_asyncio.fixture
async def two_group_connections(
    session: AsyncSession,
    connection_type: str | None,
    create_connection_data: dict | None,
    settings: Settings,
    mock_group: MockGroup,
    group_queue: Queue,  # do not delete
) -> AsyncGenerator[tuple[MockConnection, MockConnection], None]:
    connection1 = await create_connection(
        session=session,
        name=f"{secrets.token_hex(5)}_group_for_group_connection",
        type=connection_type or "postgres",
        group_id=mock_group.id,
        data=create_connection_data,
    )

    connection2 = await create_connection(
        session=session,
        name=f"{secrets.token_hex(5)}_group_for_group_connection",
        type=connection_type or "postgres",
        group_id=mock_group.id,
        data=create_connection_data,
    )

    credentials1 = await create_credentials(
        session=session,
        settings=settings,
        connection_id=connection1.id,
    )

    credentials2 = await create_credentials(
        session=session,
        settings=settings,
        connection_id=connection2.id,
    )

    yield (
        MockConnection(
            credentials=MockCredentials(
                value=decrypt_auth_data(credentials1.value, settings=settings),
                connection_id=connection1.id,
            ),
            connection=connection1,
            owner_group=mock_group,
        ),
        MockConnection(
            credentials=MockCredentials(
                value=decrypt_auth_data(credentials2.value, settings=settings),
                connection_id=connection2.id,
            ),
            connection=connection2,
            owner_group=mock_group,
        ),
    )
    await session.delete(connection1)
    await session.delete(connection2)
    await session.commit()


@pytest_asyncio.fixture
async def create_connection_auth_data(request) -> dict | None:
    if hasattr(request, "param"):
        return request.param
    return None


@pytest_asyncio.fixture
async def connection_type(request) -> str | None:
    if hasattr(request, "param"):
        return request.param
    return None


@pytest_asyncio.fixture
async def group_connection_and_group_maintainer_plus(
    session: AsyncSession,
    empty_group: MockGroup,
    group_connection: MockConnection,
    role_maintainer_plus: UserTestRoles,
    role_maintainer_or_below_without_guest: UserTestRoles,
) -> str:
    user = group_connection.owner_group.get_member_of_role(role_maintainer_plus)

    await add_user_to_group(
        user=user.user,
        group_id=empty_group.group.id,
        session=session,
        role=role_maintainer_or_below_without_guest,
    )

    return role_maintainer_plus


@pytest_asyncio.fixture
async def group_connection_with_same_name_maintainer_plus(
    session: AsyncSession,
    settings: Settings,
    empty_group: MockGroup,
    group_connection: MockConnection,
    role_maintainer_plus: UserTestRoles,
    role_maintainer_or_below_without_guest: UserTestRoles,
) -> AsyncGenerator[str, None]:
    user = group_connection.owner_group.get_member_of_role(role_maintainer_plus)

    await add_user_to_group(
        user=user.user,
        group_id=empty_group.group.id,
        session=session,
        role=role_maintainer_or_below_without_guest,
    )
    connection = await create_connection(
        session=session,
        name=group_connection.connection.name,
        group_id=empty_group.group.id,
    )

    credentials = await create_credentials(
        session=session,
        settings=settings,
        connection_id=connection.id,
    )

    yield role_maintainer_plus
    await session.delete(connection)
    await session.delete(credentials)
    await session.commit()


@pytest_asyncio.fixture
async def group_connection_with_same_name(
    session: AsyncSession,
    settings: Settings,
    empty_group: MockGroup,
    group_connection: MockConnection,
) -> AsyncGenerator[None, None]:
    connection = await create_connection(
        session=session,
        name=group_connection.connection.name,
        group_id=empty_group.group.id,
    )

    credentials = await create_credentials(
        session=session,
        settings=settings,
        connection_id=connection.id,
    )

    yield
    await session.delete(connection)
    await session.delete(credentials)
    await session.commit()


@pytest_asyncio.fixture
async def group_connection_and_group_developer_plus(
    session: AsyncSession,
    empty_group: MockGroup,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
    role_maintainer_or_below_without_guest: UserTestRoles,
) -> str:
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)

    await add_user_to_group(
        user=user.user,
        group_id=empty_group.group.id,
        session=session,
        role=role_maintainer_or_below_without_guest,
    )

    return role_developer_plus


@pytest_asyncio.fixture
async def group_connection_and_group_developer_or_below(
    session: AsyncSession,
    empty_group: MockGroup,
    group_connection: MockConnection,
    role_developer_or_below: UserTestRoles,
) -> str:
    user = group_connection.owner_group.get_member_of_role(role_developer_or_below)

    await add_user_to_group(
        user=user.user,
        group_id=empty_group.group.id,
        session=session,
        role=role_developer_or_below,
    )

    return role_developer_or_below
