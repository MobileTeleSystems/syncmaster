import pytest
from httpx import AsyncClient

from tests.mocks import MockConnection, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend, pytest.mark.hdfs]


@pytest.mark.parametrize(
    "create_connection_data,create_connection_auth_data",
    [
        (
            {"type": "hdfs", "cluster": "cluster"},
            {
                "type": "hdfs",
                "user": "user",
                "password": "password",
            },
        )
    ],
    indirect=True,
)
async def test_developer_plus_can_update_hdfs_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
    create_connection_data: dict,  # don't remove
    create_connection_auth_data: dict,  # don't remove
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    parameter_to_update = "cluster"
    value_to_update = "updated_cluser"

    # Act
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"connection_data": {"type": "hdfs", parameter_to_update: value_to_update}},
    )

    # Assert
    assert result.json() == {
        "id": group_connection.id,
        "name": group_connection.connection.name,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "connection_data": {"type": group_connection.data["type"], parameter_to_update: value_to_update},
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": group_connection.credentials.value["user"],
        },
    }
    assert result.status_code == 200
