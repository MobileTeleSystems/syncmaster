import pytest
from httpx import AsyncClient

from tests.mocks import MockConnection, UserTestRoles
from tests.test_unit.utils import fetch_connection_json

pytestmark = [pytest.mark.asyncio, pytest.mark.server, pytest.mark.samba]


@pytest.mark.parametrize(
    "connection_type,create_connection_data,create_connection_auth_data",
    [
        (
            "samba",
            {
                "host": "some_host",
                "share": "some_folder",
                "protocol": "NetBIOS",
                "domain": "domain",
                "port": None,
            },
            {
                "type": "samba",
                "user": "user",
                "password": "password",
                "auth_type": "NTLMv2",
            },
        ),
    ],
    indirect=["create_connection_data", "create_connection_auth_data"],
)
async def test_developer_plus_can_update_samba_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
    create_connection_data: dict,
    create_connection_auth_data: dict,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    connection_json = await fetch_connection_json(client, user.token, group_connection)
    new_connection_data = {
        "host": "new_host",
        "share": "new_folder",
        "protocol": "NetBIOS",
        "domain": "domain",
        "port": None,
    }

    result = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={**connection_json, "type": "samba", "connection_data": new_connection_data},
    )

    assert result.json() == {
        "id": group_connection.id,
        "name": group_connection.connection.name,
        "description": group_connection.description,
        "type": group_connection.type,
        "group_id": group_connection.group_id,
        "connection_data": new_connection_data,
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": group_connection.credentials.value["user"],
            "auth_type": group_connection.credentials.value["auth_type"],
        },
    }
    assert result.status_code == 200, result.json()
