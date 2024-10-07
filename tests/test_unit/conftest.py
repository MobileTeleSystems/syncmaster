import secrets

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.backend.api.v1.auth.utils import sign_jwt
from syncmaster.config import Settings
from syncmaster.db.models import Queue, User, UserGroup
from syncmaster.db.repositories.utils import decrypt_auth_data
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
    create_user_cm,
)

ALLOWED_SOURCES = "'hive', 'oracle', 'postgres', 'hdfs', 's3'"


async def create_group_member(
    username: str,
    group_id: int,
    session: AsyncSession,
    settings: Settings,
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

    return MockUser(
        user=user,
        auth_token=sign_jwt(user.id, settings),
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
async def superuser(session: AsyncSession, settings: Settings):
    async with create_user_cm(session, username="superuser", is_active=True, is_superuser=True) as user:
        yield MockUser(
            user=user,
            auth_token=sign_jwt(user.id, settings),
            role=UserTestRoles.Developer,
        )


@pytest_asyncio.fixture
async def simple_user(session: AsyncSession, settings: Settings):
    async with create_user_cm(session, username="simple_user", is_active=True) as user:
        yield MockUser(
            user=user,
            auth_token=sign_jwt(user.id, settings),
            role=UserTestRoles.Developer,
        )


@pytest_asyncio.fixture
async def inactive_user(session: AsyncSession, settings: Settings):
    async with create_user_cm(session, username="inactive_user") as user:
        yield MockUser(
            user=user,
            auth_token=sign_jwt(user.id, settings),
            role=UserTestRoles.Developer,
        )


@pytest_asyncio.fixture
async def deleted_user(session: AsyncSession, settings: Settings):
    async with create_user_cm(
        session,
        username="deleted_user",
        is_deleted=True,
    ) as user:
        yield MockUser(
            user=user,
            auth_token=sign_jwt(user.id, settings),
            role=UserTestRoles.Developer,
        )


@pytest_asyncio.fixture
async def user_with_many_roles(session: AsyncSession, settings: Settings, simple_user: MockUser) -> MockUser:
    user = await create_user(
        session=session,
        username="multi_role_user",
        is_active=True,
    )

    roles = [
        UserTestRoles.Owner,
        UserTestRoles.Maintainer,
        UserTestRoles.Developer,
        UserTestRoles.Guest,
    ]

    groups = []

    for role in roles:
        group = await create_group(
            session=session,
            name=f"group_for_{role}",
            owner_id=user.id if role == UserTestRoles.Owner else simple_user.user.id,
        )

        if role != UserTestRoles.Owner:
            await add_user_to_group(user=user, group_id=group.id, session=session, role=role)
        groups.append(group)

    await session.commit()

    mock_user = MockUser(
        user=user,
        auth_token=sign_jwt(user.id, settings),
    )

    yield mock_user

    for group in groups:
        await session.delete(group)

    await session.delete(user)
    await session.commit()


@pytest_asyncio.fixture
async def empty_group(session: AsyncSession, settings) -> MockGroup:
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
    yield MockGroup(
        group=group,
        owner=MockUser(
            user=owner,
            auth_token=sign_jwt(owner.id, settings),
            role=UserTestRoles.Owner,
        ),
        members=[],
    )
    await session.delete(group)
    await session.delete(owner)
    await session.commit()


@pytest_asyncio.fixture
async def group(session: AsyncSession, settings: Settings) -> MockGroup:
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
                settings=settings,
            ),
        )

    await session.commit()
    yield MockGroup(
        group=group,
        owner=MockUser(
            user=owner,
            auth_token=sign_jwt(owner.id, settings),
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
    settings: Settings,
):
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
                settings=settings,
            ),
        )

    await session.commit()

    yield MockGroup(
        group=group,
        owner=MockUser(
            user=group_owner,
            auth_token=sign_jwt(group_owner.id, settings),
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
    settings: Settings,
    mock_group: MockGroup,
) -> Queue:
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
    settings: Settings,
    group: MockGroup,
) -> Queue:
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
    create_connection_data,
    settings: Settings,
    mock_group: MockGroup,
    group_queue: Queue,  # do not delete
) -> tuple[MockConnection, MockConnection]:
    connection1 = await create_connection(
        session=session,
        name=f"{secrets.token_hex(5)}_group_for_group_connection",
        group_id=mock_group.id,
        data=create_connection_data,
    )

    connection2 = await create_connection(
        session=session,
        name=f"{secrets.token_hex(5)}_group_for_group_connection",
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

    yield MockConnection(
        credentials=MockCredentials(
            value=decrypt_auth_data(credentials1.value, settings=settings),
            connection_id=connection1.id,
        ),
        connection=connection1,
        owner_group=mock_group,
    ), MockConnection(
        credentials=MockCredentials(
            value=decrypt_auth_data(credentials2.value, settings=settings),
            connection_id=connection2.id,
        ),
        connection=connection2,
        owner_group=mock_group,
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
async def group_connection(
    session: AsyncSession,
    settings: Settings,
    create_connection_data: dict | None,
    create_connection_auth_data: dict | None,
) -> MockConnection:
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
                settings=settings,
            ),
        )

    await session.commit()
    connection = await create_connection(
        session=session,
        name=f"{secrets.token_hex(5)}_group_for_group_connection",
        group_id=group.id,
        data=create_connection_data,
    )

    credentials = await create_credentials(
        session=session,
        settings=settings,
        connection_id=connection.id,
        auth_data=create_connection_auth_data,
    )

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
                auth_token=sign_jwt(group_owner.id, settings),
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
) -> str:
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
) -> None:
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
