import pytest
from httpx import AsyncClient
from tests.utils import MockConnection, MockUser

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_read_acl_of_connection(
    client: AsyncClient,
    user_connection: MockConnection,
):
    result_response = await client.get(
        f"v1/connections/{user_connection.id}/rules",
    )
    assert result_response.status_code == 401
    assert result_response.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_superuser_read_acl_of_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    superuser: MockUser,
):
    result_response = await client.get(
        f"v1/connections/{group_connection.id}/rules",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result_response.status_code == 200
    assert len(result_response.json()["items"]) == 2
    assert result_response.json()["items"] == [
        {
            "object_id": group_connection.connection.id,
            "object_type": "connection",
            "user_id": group_connection.acls[0].user.user.id,
            "rule": 1,
        },
        {
            "object_id": group_connection.connection.id,
            "object_type": "connection",
            "user_id": group_connection.acls[1].user.user.id,
            "rule": 2,
        },
    ]


async def test_owner_read_acl_of_connection(
    client: AsyncClient,
    user_connection: MockConnection,
):
    result_response = await client.get(
        f"v1/connections/{user_connection.id}/rules",
        headers={"Authorization": f"Bearer {user_connection.owner_user.token}"},
    )
    assert result_response.status_code == 200
    assert len(result_response.json()["items"]) == 0


async def test_simple_group_member_read_acl_of_connection_error(
    client: AsyncClient,
    group_connection: MockConnection,
):
    for acl_user in group_connection.acls:
        result_response = await client.get(
            f"v1/connections/{group_connection.id}/rules",
            headers={"Authorization": f"Bearer {acl_user.user.token}"},
        )

        assert result_response.status_code == 403
        assert result_response.json()["message"] == "You have no power here"


async def test_groupowner_read_acl_of_connection_with_user_id(
    client: AsyncClient,
    group_connection: MockConnection,
):
    result_response = await client.get(
        f"v1/connections/{group_connection.id}/rules?user_id={group_connection.acls[0].user.user.id}",
        headers={"Authorization": f"Bearer {group_connection.owner_group.admin.token}"},
    )

    assert result_response.status_code == 200
    assert len(result_response.json()["items"]) == 1
    assert result_response.json()["items"] == [
        {
            "object_id": group_connection.connection.id,
            "object_type": "connection",
            "user_id": group_connection.acls[0].user.user.id,
            "rule": 1,
        },
    ]


async def test_groupowner_read_acl_of_connection(
    client: AsyncClient,
    group_connection: MockConnection,
):
    result_response = await client.get(
        f"v1/connections/{group_connection.id}/rules",
        headers={"Authorization": f"Bearer {group_connection.owner_group.admin.token}"},
    )

    assert result_response.status_code == 200
    assert len(result_response.json()["items"]) == 2
    assert result_response.json()["items"] == [
        {
            "object_id": group_connection.connection.id,
            "object_type": "connection",
            "user_id": group_connection.acls[0].user.user.id,
            "rule": 1,
        },
        {
            "object_id": group_connection.connection.id,
            "object_type": "connection",
            "user_id": group_connection.acls[1].user.user.id,
            "rule": 2,
        },
    ]


async def test_simpleuser_can_not_read_acl_of_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    simple_user: MockUser,
):
    result_response = await client.get(
        f"v1/connections/{group_connection.id}/rules",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result_response.status_code == 404
    assert result_response.json() == {
        "message": "Connection not found",
        "ok": False,
        "status_code": 404,
    }
