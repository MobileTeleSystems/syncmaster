import pytest
from httpx import AsyncClient

from tests.mocks import MockConnection, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server, pytest.mark.ftps]


@pytest.mark.parametrize(
    "connection_type,create_connection_data,create_connection_auth_data",
    [
        (
            "ftps",
            {
                "host": "some_host",
                "port": 80,
            },
            {
                "type": "basic",
                "user": "user",
                "password": "password",
            },
        ),
    ],
    indirect=["create_connection_data", "create_connection_auth_data"],
)
async def test_developer_plus_can_update_ftps_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
    create_connection_data: dict,
    create_connection_auth_data: dict,
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"type": "ftps", "connection_data": {"host": "new_host"}},
    )

    # Assert
    assert result.json() == {
        "id": group_connection.id,
        "name": group_connection.connection.name,
        "description": group_connection.description,
        "type": group_connection.type,
        "group_id": group_connection.group_id,
        "connection_data": {"host": "new_host", "port": 80},
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": group_connection.credentials.value["user"],
        },
    }
    assert result.status_code == 200
