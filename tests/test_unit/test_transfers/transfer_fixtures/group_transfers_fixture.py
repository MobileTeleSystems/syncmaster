import secrets
from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.backend.api.v1.auth.utils import sign_jwt
from syncmaster.config import Settings
from syncmaster.db.repositories.utils import decrypt_auth_data
from syncmaster.schemas.v1.connection_types import ConnectionType
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
async def group_transfers(
    session: AsyncSession,
    settings: Settings,
) -> AsyncGenerator[list[MockTransfer], None]:
    # create a group owner
    group_owner = await create_user(
        session=session,
        username="group_transfer_owner",
        is_active=True,
    )
    # Create a group
    group = await create_group(
        session=session,
        name="group_for_group_transfers",
        owner_id=group_owner.id,
    )
    # create a queue
    queue = await create_queue(
        session=session,
        name=f"{secrets.token_hex(5)}_test_queue",
        group_id=group.id,
    )
    # create members
    members = []
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

    transfers = []
    source_connections = []
    target_connections = []

    for connection_type in ConnectionType:
        # create source connection with this type
        source_connection = await create_connection(
            session=session,
            name=f"group_transfer_source_connection_{connection_type.value}",
            group_id=group.id,
            data={"type": connection_type.value},
        )
        source_connection_creds = await create_credentials(
            session=session,
            settings=settings,
            connection_id=source_connection.id,
        )
        # create target connection with the same type
        target_connection = await create_connection(
            session=session,
            name=f"group_transfer_target_connection_{connection_type.value}",
            group_id=group.id,
            data={"type": connection_type.value},
        )
        target_connection_creds = await create_credentials(
            session=session,
            settings=settings,
            connection_id=target_connection.id,
        )
        source_params = {"type": connection_type.value}
        target_params = {"type": connection_type.value}

        if connection_type == ConnectionType.S3:
            file_format = {
                "delimiter": ",",
                "encoding": "utf-8",
                "escape": "\\",
                "header": False,
                "line_sep": "\n",
                "quote": '"',
                "type": "csv",
            }
            common_params = {
                "file_format": file_format,
                "options": {},
            }
            source_params.update(common_params, directory_path="/path/to/source")
            target_params.update(common_params, directory_path="/path/to/target")
        elif connection_type == ConnectionType.HDFS:
            common_params = {"options": {}}
            source_params.update(common_params, directory_path="/path/to/source")
            target_params.update(common_params, directory_path="/path/to/target")
        elif connection_type in [ConnectionType.HIVE, ConnectionType.POSTGRES, ConnectionType.ORACLE]:
            source_params["table_name"] = "source_table"
            target_params["table_name"] = "target_table"

        transfer = await create_transfer(
            session=session,
            name=f"group_transfer_{connection_type.value}",
            group_id=group.id,
            source_connection_id=source_connection.id,
            target_connection_id=target_connection.id,
            queue_id=queue.id,
            source_params=source_params,
            target_params=target_params,
            is_scheduled=True,
            schedule="0 0 * * *",
            strategy_params={"type": "full"},
        )
        # create MockTransfer
        mock_transfer = MockTransfer(
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
        transfers.append(mock_transfer)
        source_connections.append(source_connection)
        target_connections.append(target_connection)

    await session.commit()

    yield transfers

    # cleanup
    for transfer in transfers:
        await session.delete(transfer.transfer)
    for connection in source_connections + target_connections:
        await session.delete(connection)
    await session.delete(queue)
    await session.delete(group)
    await session.delete(group_owner)
    for member in members:
        await session.delete(member.user)
    await session.commit()
