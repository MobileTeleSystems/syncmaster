import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.mocks import MockConnection, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server, pytest.mark.hdfs]


@pytest.mark.parametrize(
    "connection_type,create_connection_data,create_connection_auth_data",
    [
        (
            "hdfs",
            {
                "cluster": "cluster",
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
async def test_guest_plus_can_read_hdfs_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_guest_plus: UserTestRoles,
    session: AsyncSession,
    create_connection_data: dict,  # don't remove
    create_connection_auth_data: dict,  # don't remove
):
    user = group_connection.owner_group.get_member_of_role(role_guest_plus)

    response = await client.get(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": group_connection.id,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "name": group_connection.name,
        "type": group_connection.type,
        "connection_data": {"cluster": group_connection.data["cluster"]},
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": group_connection.credentials.value["user"],
        },
    }
