import pytest
from httpx import AsyncClient

from tests.mocks import MockTransfer, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_guest_plus_can_read_transfers(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        params={"group_id": group_transfer.owner_group.group.id},
    )

    # Assert
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 1,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [
            {
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
            },
        ],
    }
    assert result.status_code == 200


async def test_groupless_user_cannot_read_transfers(
    client: AsyncClient,
    simple_user: MockUser,
    group_transfer: MockTransfer,
):
    # Act
    result = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        params={"group_id": group_transfer.owner_group.group.id},
    )

    # Assert
    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }
    assert result.status_code == 404


async def test_superuser_can_read_transfers(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
):
    # Act
    result = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"group_id": group_transfer.owner_group.group.id},
    )

    # Assert
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 1,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [
            {
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
            },
        ],
    }
    assert result.status_code == 200


async def test_unauthorized_user_cannot_read_transfers(client: AsyncClient):
    # Act
    result = await client.get("v1/transfers")

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }
    assert result.status_code == 401


async def test_developer_plus_cannot_read_unknown_group_transfers_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_developer_plus: UserTestRoles,
):
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        params={"group_id": -1},
    )

    # Assert
    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }


async def test_superuser_cannot_read_unknown_group_transfers_error(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
):
    # Act
    result = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"group_id": -1},
    )

    # Assert
    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }
