import pytest
from httpx import AsyncClient

from tests.mocks import MockConnection, UserTestRoles
from tests.test_unit.utils import fetch_connection_json

pytestmark = [pytest.mark.asyncio, pytest.mark.server, pytest.mark.s3]


@pytest.mark.parametrize(
    "connection_type,create_connection_data,create_connection_auth_data",
    [
        (
            "s3",
            {
                "bucket": "some_bucket",
                "host": "some_host",
                "port": 80,
                "region": "some_region",
                "protocol": "http",
                "bucket_style": "domain",
            },
            {
                "type": "s3",
                "access_key": "access_key",
                "secret_key": "secret_key",
            },
        ),
    ],
    indirect=["create_connection_data", "create_connection_auth_data"],
)
async def test_developer_plus_can_update_s3_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    connection_json = await fetch_connection_json(client, user.token, group_connection)
    new_connection_data = {
        "bucket": "new_bucket",
        "host": "new_host",
        "port": 80,
        "region": "new_region",
        "protocol": "http",
        "bucket_style": "domain",
    }

    result = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={**connection_json, "type": "s3", "connection_data": new_connection_data},
    )

    assert result.json() == {
        "id": group_connection.id,
        "name": group_connection.connection.name,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "type": group_connection.type,
        "connection_data": new_connection_data,
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "access_key": group_connection.credentials.value["access_key"],
        },
    }
    assert result.status_code == 200, result.json()
