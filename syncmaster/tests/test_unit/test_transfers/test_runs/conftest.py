import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_unit.utils import (
    create_connection,
    create_group,
    create_run,
    create_transfer,
    create_user,
)
from tests.utils import MockConnection, MockGroup, MockRun, MockTransfer, MockUser

from app.api.v1.auth.utils import sign_jwt
from app.config import Settings
from app.db.models import UserGroup


@pytest_asyncio.fixture
async def group_run(session: AsyncSession, settings: Settings) -> MockTransfer:
    group_admin = await create_user(session=session, username="group_admin_connection", is_active=True)
    group = await create_group(session=session, name="connection_group", admin_id=group_admin.id)
    members: list[MockUser] = []
    for username in (
        "connection_group_member_1",  # with read rule
        "connection_group_member_2",  # with write rule
        "connection_group_member_3",  # with delete rule
    ):
        u = await create_user(session, username, is_active=True)
        members.append(MockUser(user=u, auth_token=sign_jwt(u.id, settings)))
        session.add(UserGroup(group_id=group.id, user_id=u.id))
    await session.commit()
    mock_group = MockGroup(
        group=group,
        admin=MockUser(user=group_admin, auth_token=sign_jwt(group_admin.id, settings)),
        members=members,
    )

    source_connection = await create_connection(
        session=session,
        name="group_transfer_source_connection",
        group_id=group.id,
    )
    target_connection = await create_connection(
        session=session,
        name="group_transfer_target_connection",
        group_id=group.id,
    )

    transfer = await create_transfer(
        session=session,
        name="group_transfer",
        group_id=group.id,
        source_connection_id=source_connection.id,
        target_connection_id=target_connection.id,
    )
    mock_transfer = MockTransfer(
        transfer=transfer,
        source_connection=MockConnection(connection=source_connection, owner_group=mock_group),
        target_connection=MockConnection(connection=target_connection, owner_group=mock_group),
        owner_group=mock_group,
    )
    run = await create_run(session=session, transfer_id=transfer.id)

    yield MockRun(run=run, transfer=mock_transfer)

    await session.delete(run)
    await session.delete(transfer)
    await session.delete(source_connection)
    await session.delete(target_connection)
    await session.delete(group)
    await session.delete(group_admin)
    for member in members:
        await session.delete(member.user)
    await session.commit()
