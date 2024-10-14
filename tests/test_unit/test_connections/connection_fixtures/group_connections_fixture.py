import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Connection
from syncmaster.schemas.v1.connection_types import ConnectionType
from tests.mocks import MockConnection


@pytest_asyncio.fixture
async def group_connections(group_connection: MockConnection, session: AsyncSession) -> list[MockConnection]:
    connection = group_connection.connection

    # start with the connection from group_connection fixture
    connections = [group_connection]
    connection_types = list(ConnectionType)

    # since group_connection already created a connection, we start from index 1
    for conn_type in connection_types[1:]:

        new_data = {  # TODO: create different dicts
            **connection.data,
            "type": conn_type.value,
            "cluster": "cluster",
            "bucket": "bucket",
        }

        new_connection = Connection(
            group_id=connection.group_id,
            name=f"{connection.name}_{conn_type.value}",
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
