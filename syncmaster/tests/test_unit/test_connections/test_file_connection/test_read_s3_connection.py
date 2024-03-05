import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockConnection, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend, pytest.mark.s3]


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
async def test_guest_plus_can_read_s3_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_guest_plus: UserTestRoles,
    session: AsyncSession,
    create_connection_data: dict,  # don't remove
    create_connection_auth_data: dict,  # don't remove
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.get(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.json() == {
        "id": group_connection.id,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "name": group_connection.name,
        "connection_data": {
            "type": group_connection.data["type"],
            "host": group_connection.data["host"],
            "bucket": group_connection.data["bucket"],
            "port": group_connection.data["port"],
            "region": group_connection.data["region"],
            "protocol": group_connection.data["protocol"],
            "bucket_style": group_connection.data["bucket_style"],
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "access_key": group_connection.credentials.value["access_key"],
        },
    }
    assert result.status_code == 200
