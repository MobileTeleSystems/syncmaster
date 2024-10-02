import random
import string

import pytest
from httpx import AsyncClient

from tests.mocks import MockGroup, MockTransfer, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_guest_plus_can_read_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_guest_plus: UserTestRoles,
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
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }
    assert result.status_code == 404


async def test_group_member_cannot_read_transfer_of_other_group(
    client: AsyncClient,
    group_transfer: MockTransfer,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
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
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
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


@pytest.mark.parametrize(
    "search_value_extractor",
    [
        lambda transfer: transfer.name,
        lambda transfer: transfer.source_params.get("table_name"),
        lambda transfer: transfer.target_params.get("table_name"),
        lambda transfer: transfer.source_params.get("directory_path"),
        lambda transfer: transfer.target_params.get("directory_path"),
    ],
    ids=["name", "source_table_name", "target_table_name", "source_directory_path", "target_directory_path"],
)
async def test_search_transfers_with_query(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
    search_value_extractor,
):
    transfer = group_transfer.transfer
    search_query = search_value_extractor(transfer)

    result = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"group_id": group_transfer.group_id, "search_query": search_query},
    )

    transfer_data = result.json()["items"][0]

    assert transfer_data == {
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


async def test_search_transfers_with_nonexistent_query(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
):
    random_search_query = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))

    result = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"group_id": group_transfer.group_id, "search_query": random_search_query},
    )

    assert result.status_code == 200
    assert result.json()["items"] == []


async def test_unauthorized_user_cannot_read_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    # Act
    result = await client.get(f"v1/transfers/{group_transfer.id}")

    # Assert
    assert result.status_code == 401
    assert result.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
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
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }


async def test_group_member_cannot_read_unknown_transfer_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_guest_plus: UserTestRoles,
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
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }
    assert result.status_code == 404
