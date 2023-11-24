import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockGroup, MockTransfer, MockUser, TestUserRoles

from app.db.models import Transfer

pytestmark = [pytest.mark.asyncio]


async def test_maintainer_plus_can_delete_group_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_maintainer_plus: TestUserRoles,
    session: AsyncSession,
):
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_maintainer_plus)
    transfer = await session.get(Transfer, group_transfer.id)

    assert not transfer.is_deleted

    # Act
    result = await client.delete(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Transfer was deleted",
    }
    await session.refresh(transfer)
    assert transfer.is_deleted


async def test_superuser_can_delete_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    superuser: MockUser,
    session: AsyncSession,
):
    # Act
    result = await client.delete(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    # Assert
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Transfer was deleted",
    }
    await session.refresh(group_transfer.transfer)
    assert group_transfer.is_deleted


async def test_groupless_user_cannot_delete_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    simple_user: MockUser,
):
    # Act
    result = await client.delete(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )

    # Assert
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }


async def test_user_or_below_cannot_delete_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    session: AsyncSession,
    role_user_or_below: TestUserRoles,
):
    # Act
    user = group_transfer.owner_group.get_member_of_role(role_user_or_below)

    # Assert
    result = await client.delete(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.json() == {
        "message": "You have no power here",
        "ok": False,
        "status_code": 403,
    }
    assert result.status_code == 403
    await session.refresh(group_transfer.transfer)
    assert not group_transfer.is_deleted


async def test_group_member_cannot_delete_other_group_transfer(
    client: AsyncClient,
    group: MockGroup,
    group_transfer: MockTransfer,
    role_guest_plus: TestUserRoles,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.delete(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }
    assert result.status_code == 404


async def test_unauthorized_user_cannot_delete_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    # Act
    result = await client.delete(
        f"v1/transfers/{group_transfer.id}",
    )

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }
    assert result.status_code == 401


async def test_superuser_cannot_delete_unknown_transfer_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    session: AsyncSession,
    superuser: MockUser,
):
    # Act
    result = await client.delete(
        "v1/transfers/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    # Assert
    assert result.json() == {
        "message": "Transfer not found",
        "ok": False,
        "status_code": 404,
    }
    assert result.status_code == 404


async def test_maintainer_plus_cannot_delete_unknown_transfer_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_maintainer_plus: TestUserRoles,
    session: AsyncSession,
):
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_maintainer_plus)

    # Act
    result = await client.delete(
        "v1/transfers/-1",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.json() == {
        "message": "Transfer not found",
        "ok": False,
        "status_code": 404,
    }
