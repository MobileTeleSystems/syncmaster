from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Connection, ConnectionType
from tests.mocks import MockConnection


@pytest_asyncio.fixture
async def group_connections(
    group_connection: MockConnection,
    session: AsyncSession,
) -> AsyncGenerator[list[MockConnection], None]:
    connection = group_connection.connection

    # start with the connection from group_connection fixture
    connections = [group_connection]
    connection_types = list(ConnectionType)

    # since group_connection already created a connection, we start from index 1
    for conn_type in connection_types[1:]:

        new_data = {
            **connection.data,
        }

        if conn_type in [ConnectionType.HDFS, ConnectionType.HIVE]:
            new_data.update(
                {
                    "cluster": "cluster",
                },
            )
        elif conn_type == ConnectionType.ICEBERG_REST_S3:
            new_data.update(
                {
                    "rest_catalog_url": "https://rest.domain.com",
                    "s3_warehouse_path": "/some/warehouse",
                    "s3_host": "s3.domain.com",
                    "s3_bucket": "bucket",
                    "s3_region": "us-east-1",
                },
            )
        elif conn_type == ConnectionType.S3:
            new_data.update(
                {
                    "bucket": "bucket",
                },
            )
        elif conn_type == ConnectionType.SAMBA:
            new_data.update(
                {
                    "share": "folder",
                    "protocol": "SMB",
                    "domain": "domain",
                },
            )
        elif conn_type == ConnectionType.WEBDAV:
            new_data.update(
                {
                    "protocol": "http",
                },
            )
        elif conn_type in [
            ConnectionType.POSTGRES,
            ConnectionType.CLICKHOUSE,
            ConnectionType.MSSQL,
            ConnectionType.MYSQL,
        ]:
            new_data.update(
                {
                    "database_name": "database",
                },
            )

        new_connection = Connection(
            group_id=connection.group_id,
            name=f"{connection.name}_{conn_type.value}",
            type=conn_type.value,
            description=connection.description,
            data=new_data,
        )
        session.add(new_connection)

        mock_connection = MockConnection(
            credentials=group_connection.credentials,
            connection=new_connection,
            owner_group=group_connection.owner_group,
        )
        connections.append(mock_connection)

    await session.commit()

    yield connections

    for mock_connection in connections[1:]:
        await session.delete(mock_connection.connection)
    await session.commit()
