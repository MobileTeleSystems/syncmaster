import pytest
from httpx import AsyncClient

from tests.mocks import MockConnection, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server, pytest.mark.mysql]


@pytest.mark.parametrize(
    "connection_type,create_connection_data,create_connection_auth_data",
    [
        (
            "mysql",
            {
                "host": "127.0.0.1",
                "port": 3306,
                "database_name": "database",
            },
            {
                "type": "basic",
                "user": "user",
                "password": "secret",
            },
        ),
    ],
    indirect=["create_connection_data", "create_connection_auth_data"],
)
async def test_developer_plus_can_update_mysql_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    group_connection.connection.group.id

    # Act
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "type": group_connection.type,
            "connection_data": {
                "host": "127.0.1.1",
                "database_name": "new_database",
            },
            "auth_data": {
                "type": "basic",
                "user": "new_user",
            },
        },
    )

    # Assert
    assert result.status_code == 200
    assert result.json() == {
        "id": group_connection.id,
        "name": group_connection.name,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "type": "mysql",
        "connection_data": {
            "host": "127.0.1.1",
            "port": group_connection.data["port"],
            "database_name": "new_database",
            "additional_params": {},
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": "new_user",
        },
    }
