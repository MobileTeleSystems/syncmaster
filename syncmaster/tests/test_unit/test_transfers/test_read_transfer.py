import pytest
from httpx import AsyncClient
from tests.utils import MockGroup, MockTransfer, MockUser, TestUserRoles

pytestmark = [pytest.mark.asyncio]


async def test_guest_plus_can_read_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_guest_plus: TestUserRoles,
):
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.get(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.json() == {
        "id": group_transfer.id,
        "group_id": group_transfer.group_id,
        "name": group_transfer.name,
        "description": group_transfer.description,
        "schedule": group_transfer.schedule,
        "is_scheduled": group_transfer.is_scheduled,
        "source_connection_id": group_transfer.source_connection_id,
        "target_connection_id": group_transfer.target_connection_id,
        "source_params": group_transfer.source_params,
        "target_params": group_transfer.target_params,
        "strategy_params": group_transfer.strategy_params,
        "queue_id": group_transfer.transfer.queue_id,
    }
    assert result.status_code == 200


async def test_groupless_user_cannot_read_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    simple_user: MockUser,
):
    # Act
    result = await client.get(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }
    assert result.status_code == 404


async def test_group_member_cannot_read_transfer_of_other_group(
    client: AsyncClient,
    group_transfer: MockTransfer,
    group: MockGroup,
    role_guest_plus: TestUserRoles,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.get(
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


async def test_superuser_can_read_transfer(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
):
    # Act
    result = await client.get(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    # Assert
    assert result.json() == {
        "id": group_transfer.id,
        "group_id": group_transfer.group_id,
        "name": group_transfer.name,
        "description": group_transfer.description,
        "schedule": group_transfer.schedule,
        "is_scheduled": group_transfer.is_scheduled,
        "source_connection_id": group_transfer.source_connection_id,
        "target_connection_id": group_transfer.target_connection_id,
        "source_params": group_transfer.source_params,
        "target_params": group_transfer.target_params,
        "strategy_params": group_transfer.strategy_params,
        "queue_id": group_transfer.transfer.queue_id,
    }
    assert result.status_code == 200


async def test_unauthorized_user_cannot_read_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    # Act
    result = await client.get(f"v1/transfers/{group_transfer.id}")

    # Assert
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_superuser_read_not_exist_transfer_error(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
):
    result = await client.get(
        "v1/transfers/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }


async def test_group_member_cannot_read_unknown_transfer_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_guest_plus: TestUserRoles,
):
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.get(
        "v1/transfers/-1",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.json() == {
        "message": "Transfer not found",
        "ok": False,
        "status_code": 404,
    }
    assert result.status_code == 404
