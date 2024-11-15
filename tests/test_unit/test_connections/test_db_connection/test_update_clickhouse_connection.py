import pytest
from httpx import AsyncClient

from tests.mocks import MockConnection, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend, pytest.mark.clickhouse]


@pytest.mark.parametrize(
    "create_connection_data,create_connection_auth_data",
    [
        (
            {
                "type": "clickhouse",
                "host": "127.0.0.1",
                "port": 8123,
            },
            {
                "type": "clickhouse",
                "user": "user",
                "password": "secret",
            },
        ),
    ],
    indirect=True,
)
async def test_developer_plus_can_update_clickhouse_connection(
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
            "connection_data": {
                "type": "clickhouse",
                "host": "127.0.1.1",
                "database_name": "new_name",
            },
            "auth_data": {
                "type": "clickhouse",
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
        "connection_data": {
            "type": group_connection.data["type"],
            "host": "127.0.1.1",
            "port": group_connection.data["port"],
            "database_name": "new_name",
            "additional_params": {},
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": "new_user",
        },
    }
