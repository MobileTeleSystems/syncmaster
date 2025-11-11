import pytest
from httpx import AsyncClient

from tests.mocks import MockConnection, UserTestRoles
from tests.test_unit.utils import fetch_connection_json

pytestmark = [pytest.mark.asyncio, pytest.mark.server, pytest.mark.iceberg]


@pytest.mark.parametrize(
    "connection_type,create_connection_data,create_connection_auth_data",
    [
        (
            "iceberg_rest_s3",
            {
                "metastore_url": "http://domain.com:8000",
                "s3_warehouse_path": "/some/warehouse",
                "s3_protocol": "http",
                "s3_host": "localhost",
                "s3_port": 9010,
                "s3_bucket": "some_bucket",
                "s3_region": "us-east-1",
                "s3_bucket_style": True,
            },
            {
                "type": "iceberg_rest_basic_s3_basic",
                "metastore_username": "user",
                "metastore_password": "secret",
                "s3_access_key": "access_key",
                "s3_secret_key": "secret_key",
            },
        ),
    ],
    indirect=["create_connection_data", "create_connection_auth_data"],
)
async def test_developer_plus_can_update_iceberg_rest_s3_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    connection_json = await fetch_connection_json(client, user.token, group_connection)

    result = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            **connection_json,
            "type": group_connection.type,
            "connection_data": {
                "metastore_url": "http://rest.domain.com:8000",
                "s3_warehouse_path": "/some/new/warehouse",
                "s3_protocol": "https",
                "s3_host": "s3.domain.com",
                "s3_bucket": "new_bucket",
                "s3_region": "us-east-2",
            },
            "auth_data": {
                "type": "iceberg_rest_basic_s3_basic",
                "metastore_username": "new_user",
                "metastore_password": "new_password",
                "s3_access_key": "new_access_key",
            },
        },
    )

    assert result.status_code == 200, result.json()
    assert result.json() == {
        "id": group_connection.id,
        "name": group_connection.name,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "type": group_connection.type,
        "connection_data": {
            "metastore_url": "http://rest.domain.com:8000",
            "s3_warehouse_path": "/some/new/warehouse",
            "s3_protocol": "https",
            "s3_host": "s3.domain.com",
            "s3_port": None,
            "s3_bucket": "new_bucket",
            "s3_region": "us-east-2",
            "s3_bucket_style": False,
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "metastore_username": "new_user",
            "s3_access_key": "new_access_key",
        },
    }
