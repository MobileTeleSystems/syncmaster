import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockConnection, MockGroup, MockTransfer, MockUser, TestUserRoles

from app.db.models import Connection

pytestmark = [pytest.mark.asyncio]


async def test_user_plus_can_update_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_user_plus: TestUserRoles,
):
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_user_plus)

    # Act
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"name": "New transfer name"},
    )

    # Assert
    assert result.status_code == 200
    assert result.json() == {
        "id": group_transfer.id,
        "group_id": group_transfer.group_id,
        "name": "New transfer name",
        "description": group_transfer.description,
        "schedule": group_transfer.schedule,
        "is_scheduled": group_transfer.is_scheduled,
        "source_connection_id": group_transfer.source_connection_id,
        "target_connection_id": group_transfer.target_connection_id,
        "source_params": group_transfer.source_params,
        "target_params": group_transfer.target_params,
        "strategy_params": group_transfer.strategy_params,
    }


async def test_groupless_user_cannot_update_connection(
    client: AsyncClient,
    group_transfer: MockTransfer,
    simple_user: MockUser,
):
    # Act
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={"name": "New transfer name"},
    )

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }
    assert result.status_code == 404


async def test_superuser_can_update_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    superuser: MockUser,
):
    # Act
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={"name": "New transfer name"},
    )

    # Assert
    assert result.status_code == 200
    assert result.json() == {
        "id": group_transfer.id,
        "group_id": group_transfer.group_id,
        "name": "New transfer name",
        "description": group_transfer.description,
        "schedule": group_transfer.schedule,
        "is_scheduled": group_transfer.is_scheduled,
        "source_connection_id": group_transfer.source_connection_id,
        "target_connection_id": group_transfer.target_connection_id,
        "source_params": group_transfer.source_params,
        "target_params": group_transfer.target_params,
        "strategy_params": group_transfer.strategy_params,
    }


async def test_other_group_member_cannot_update_transfer(
    client: AsyncClient,
    group: MockGroup,
    group_transfer: MockTransfer,
    role_user_plus: TestUserRoles,
):
    # Arrange
    user = group.get_member_of_role(role_user_plus)

    # Act
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"name": "New transfer name"},
    )

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }
    assert result.status_code == 404


async def test_check_connection_types_and_its_params_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_user_plus: TestUserRoles,
):
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_user_plus)
    # Act
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "New transfer name",
            "source_params": {"type": "oracle", "table_name": "New table name"},
        },
    )

    # Assert
    assert result.status_code == 400
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "Source connection has type `postgres` but its params has `oracle` type",
    }

    # Act
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "New transfer name",
            "source_params": {"type": "postgres", "table_name": "New table name"},
        },
    )

    # Assert
    assert result.json() == {
        "id": group_transfer.id,
        "group_id": group_transfer.group_id,
        "name": "New transfer name",
        "description": group_transfer.description,
        "schedule": group_transfer.schedule,
        "is_scheduled": group_transfer.is_scheduled,
        "source_connection_id": group_transfer.source_connection_id,
        "target_connection_id": group_transfer.target_connection_id,
        "source_params": {
            "type": group_transfer.source_params["type"],
            "table_name": "New table name",
        },
        "target_params": group_transfer.target_params,
        "strategy_params": group_transfer.strategy_params,
    }
    assert result.status_code == 200


async def test_check_different_connection_groups_for_transfer(
    client: AsyncClient,
    group_transfer_and_group_connection_user_plus: tuple[str, Connection],
    session: AsyncSession,
    group_transfer: MockTransfer,
):
    # Arrange
    role, connection = group_transfer_and_group_connection_user_plus
    user = group_transfer.owner_group.get_member_of_role(role)

    # Act
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"source_connection_id": connection.id},
    )

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "Connections should belong to the transfer group",
    }
    assert result.status_code == 400


async def test_group_member_not_in_new_connection_group_cannot_update_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    group_connection: MockConnection,
    session: AsyncSession,
    role_user_plus: TestUserRoles,
):
    # Assert
    user = group_transfer.owner_group.get_member_of_role(role_user_plus)

    # Act
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"source_connection_id": group_connection.connection.id},
    )

    # Arrange
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }
    assert result.status_code == 404


async def test_unauthorized_user_cannot_update_connection(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    # Act
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        json={"name": "New transfer name"},
    )

    # Assert
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_group_member_cannot_update_unknow_transfer_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_user_plus: TestUserRoles,
):
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_user_plus)

    # Act
    result = await client.patch(
        f"v1/transfers/-1",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"name": "New transfer name"},
    )

    # Assert
    assert result.json() == {
        "message": "Transfer not found",
        "ok": False,
        "status_code": 404,
    }
    assert result.status_code == 404


async def test_superuser_cannot_update_unknown_transfer_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    superuser: MockUser,
):
    # Act
    result = await client.patch(
        f"v1/transfers/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={"name": "New transfer name"},
    )

    # Assert
    assert result.json() == {
        "message": "Transfer not found",
        "ok": False,
        "status_code": 404,
    }
    assert result.status_code == 404
