import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockGroup, MockTransfer, MockUser

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_delete_connection(
    client: AsyncClient,
    user_transfer: MockTransfer,
):
    result = await client.delete(
        f"v1/transfers/{user_transfer.id}",
    )
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_simple_user_cannot_delete_transfer_other_user(
    client: AsyncClient, user_transfer: MockTransfer, simple_user: MockUser
):
    result = await client.delete(
        f"v1/transfers/{user_transfer.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }


async def test_user_can_delete_own_transfer(
    client: AsyncClient,
    user_transfer: MockTransfer,
    session: AsyncSession,
):
    result = await client.delete(
        f"v1/transfers/{user_transfer.id}",
        headers={"Authorization": f"Bearer {user_transfer.owner_user.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Transfer was deleted",
    }
    await session.refresh(user_transfer.transfer)
    assert user_transfer.is_deleted

    result = await client.delete(
        f"v1/transfers/{user_transfer.id}",
        headers={"Authorization": f"Bearer {user_transfer.owner_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }


async def test_superuser_can_delete_user_transfer(
    client: AsyncClient,
    user_transfer: MockTransfer,
    superuser: MockUser,
    session: AsyncSession,
):
    result = await client.delete(
        f"v1/transfers/{user_transfer.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Transfer was deleted",
    }
    await session.refresh(user_transfer.transfer)
    assert user_transfer.is_deleted

    # try delete twice
    result = await client.delete(
        f"v1/transfers/{user_transfer.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }


async def test_group_admin_can_delete_own_group_transfer(
    client: AsyncClient, group_transfer: MockTransfer
):
    admin = group_transfer.owner_group.admin
    result = await client.delete(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {admin.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Transfer was deleted",
    }


async def test_group_admin_cannot_delete_other_group_transfer(
    client: AsyncClient, empty_group: MockGroup, group_transfer: MockTransfer
):
    other_admin = empty_group.admin
    result = await client.delete(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {other_admin.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }


async def test_superuser_can_delete_group_transfer(
    client: AsyncClient, group_transfer: MockTransfer, superuser: MockUser
):
    result = await client.delete(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Transfer was deleted",
    }
