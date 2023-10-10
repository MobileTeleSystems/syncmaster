import pytest
from httpx import AsyncClient
from tests.utils import MockTransfer, MockUser

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_read_acl_of_transfer(
    client: AsyncClient,
    user_transfer: MockTransfer,
):
    result_response = await client.get(
        f"v1/transfers/{user_transfer.id}/rules",
    )
    assert result_response.status_code == 401
    assert result_response.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_superuser_read_acl_of_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    superuser: MockUser,
):
    result_response = await client.get(
        f"v1/transfers/{group_transfer.id}/rules",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    assert result_response.status_code == 200
    assert len(result_response.json()["items"]) == 2
    assert result_response.json()["items"] == [
        {
            "object_id": group_transfer.transfer.id,
            "object_type": "transfer",
            "user_id": group_transfer.acls[0].user.user.id,
            "rule": 1,
        },
        {
            "object_id": group_transfer.transfer.id,
            "object_type": "transfer",
            "user_id": group_transfer.acls[1].user.user.id,
            "rule": 2,
        },
    ]


async def test_owner_read_acl_of_transfer(
    client: AsyncClient,
    user_transfer: MockTransfer,
):
    result_response = await client.get(
        f"v1/transfers/{user_transfer.id}/rules",
        headers={"Authorization": f"Bearer {user_transfer.owner_user.token}"},
    )
    assert result_response.status_code == 200
    assert len(result_response.json()["items"]) == 0


async def test_simple_group_member_read_acl_of_transfer_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    for acl_user in group_transfer.acls:
        result_response = await client.get(
            f"v1/transfers/{group_transfer.id}/rules",
            headers={"Authorization": f"Bearer {acl_user.user.token}"},
        )

        assert result_response.status_code == 403
        assert result_response.json()["message"] == "You have no power here"


async def test_groupowner_read_acl_of_transfer_with_user_id(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    result_response = await client.get(
        f"v1/transfers/{group_transfer.id}/rules?user_id={group_transfer.acls[0].user.user.id}",
        headers={"Authorization": f"Bearer {group_transfer.owner_group.admin.token}"},
    )

    assert result_response.status_code == 200
    assert len(result_response.json()["items"]) == 1
    assert result_response.json()["items"] == [
        {
            "object_id": group_transfer.id,
            "object_type": "transfer",
            "user_id": group_transfer.acls[0].user.user.id,
            "rule": 1,
        },
    ]


async def test_groupowner_read_acl_of_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    result_response = await client.get(
        f"v1/transfers/{group_transfer.id}/rules",
        headers={"Authorization": f"Bearer {group_transfer.owner_group.admin.token}"},
    )

    assert result_response.status_code == 200
    assert len(result_response.json()["items"]) == 2
    assert result_response.json()["items"] == [
        {
            "object_id": group_transfer.id,
            "object_type": "transfer",
            "user_id": group_transfer.acls[0].user.user.id,
            "rule": 1,
        },
        {
            "object_id": group_transfer.id,
            "object_type": "transfer",
            "user_id": group_transfer.acls[1].user.user.id,
            "rule": 2,
        },
    ]


async def test_simpleuser_can_not_read_acl_of_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    simple_user: MockUser,
):
    result_response = await client.get(
        f"v1/transfers/{group_transfer.id}/rules",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result_response.status_code == 404
    assert result_response.json() == {
        "message": "Transfer not found",
        "ok": False,
        "status_code": 404,
    }
