from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.backend.settings import ServerAppSettings as Settings
from syncmaster.db.models import ConnectionType
from syncmaster.db.repositories.utils import decrypt_auth_data
from tests.mocks import MockConnection, MockCredentials, MockTransfer
from tests.test_unit.utils import create_connection, create_credentials, create_transfer


@pytest_asyncio.fixture
async def group_transfers(
    group_transfer: MockTransfer,
    session: AsyncSession,
    settings: Settings,
) -> AsyncGenerator[list[MockTransfer], None]:
    group = group_transfer.owner_group.group
    queue = group_transfer.transfer.queue
    mock_group = group_transfer.owner_group

    transfers = [group_transfer]
    source_connections = [group_transfer.source_connection.connection]
    target_connections = [group_transfer.target_connection.connection]

    for connection_type in ConnectionType:
        source_connection = await create_connection(
            session=session,
            name=f"group_transfer_source_connection_{connection_type.value}",
            type=connection_type.value,
            group_id=group.id,
        )
        source_connection_creds = await create_credentials(
            session=session,
            settings=settings,
            connection_id=source_connection.id,
        )

        target_connection = await create_connection(
            session=session,
            name=f"group_transfer_target_connection_{connection_type.value}",
            type=connection_type.value,
            group_id=group.id,
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
                "include_header": False,
                "line_sep": "\n",
                "quote": '"',
                "type": "csv",
                "compression": "none",
            }
            common_params = {
                "file_format": file_format,
                "options": {},
            }
            source_params.update(common_params)
            source_params["directory_path"] = "/path/to/source"
            target_params.update(common_params)
            target_params["directory_path"] = "/path/to/target"
        elif connection_type == ConnectionType.HDFS:
            common_params = {"options": {}}
            source_params.update(common_params)
            source_params["directory_path"] = "/path/to/source"
            target_params.update(common_params)
            target_params["directory_path"] = "/path/to/target"
        elif connection_type in [
            ConnectionType.HIVE,
            ConnectionType.POSTGRES,
            ConnectionType.ORACLE,
            ConnectionType.CLICKHOUSE,
            ConnectionType.MSSQL,
            ConnectionType.MYSQL,
        ]:
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

    for transfer in transfers[1:]:  # skip the transfer from group_transfer
        await session.delete(transfer.transfer)
    for connection in source_connections[1:] + target_connections[1:]:  # skip connections from group_transfer
        await session.delete(connection)

    await session.commit()
