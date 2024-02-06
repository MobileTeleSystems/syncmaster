import pytest
from httpx import AsyncClient
from tests.utils import MockConnection, UserTestRoles

pytestmark = [pytest.mark.asyncio]


@pytest.mark.parametrize(
    "create_connection_data,create_connection_auth_data",
    [
        (
            {
                "type": "s3",
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
        )
    ],
    indirect=True,
)
async def test_user_plus_can_update_s3_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_user_plus: UserTestRoles,
    create_connection_data: dict,  # don't remove
    create_connection_auth_data: dict,  # don't remove
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_user_plus)
    region = "new_region"

    # Act
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"connection_data": {"type": "s3", "region": region}},
    )

    # Assert
    assert result.json() == {
        "id": group_connection.id,
        "name": group_connection.connection.name,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "connection_data": {
            "type": group_connection.data["type"],
            "host": group_connection.data["host"],
            "bucket": group_connection.data["bucket"],
            "port": group_connection.data["port"],
            "region": region,
            "protocol": group_connection.data["protocol"],
            "bucket_style": group_connection.data["bucket_style"],
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "access_key": group_connection.credentials.value["access_key"],
        },
    }
    assert result.status_code == 200
