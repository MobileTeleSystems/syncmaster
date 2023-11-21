import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockConnection, MockGroup, MockTransfer, MockUser, TestUserRoles

from app.db.models import Transfer

pytestmark = [pytest.mark.asyncio]


async def test_user_plus_can_create_transfer(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    session: AsyncSession,
    role_user_plus: TestUserRoles,
):
    # Arrange
    first_connection, second_connection = two_group_connections
    user = first_connection.owner_group.get_member_of_role(role_user_plus)

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": first_connection.owner_group.group.id,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_connection.id,
            "target_connection_id": second_connection.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
        },
    )

    # Pre-Assert
    transfer = (
        await session.scalars(
            select(Transfer).filter_by(
                name="new test transfer",
                group_id=first_connection.owner_group.group.id,
            )
        )
    ).one()

    # Assert
    assert result.status_code == 200
    assert result.json() == {
        "id": transfer.id,
        "group_id": transfer.group_id,
        "name": transfer.name,
        "description": transfer.description,
        "schedule": transfer.schedule,
        "is_scheduled": transfer.is_scheduled,
        "source_connection_id": transfer.source_connection_id,
        "target_connection_id": transfer.target_connection_id,
        "source_params": transfer.source_params,
        "target_params": transfer.target_params,
        "strategy_params": transfer.strategy_params,
    }


async def test_guest_cannot_create_transfer(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    session: AsyncSession,
):
    # Arrange
    first_connection, second_connection = two_group_connections
    user = first_connection.owner_group.get_member_of_role(TestUserRoles.Guest)

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": first_connection.owner_group.group.id,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_connection.id,
            "target_connection_id": second_connection.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
        },
    )

    # Assert
    assert result.json() == {
        "message": "You have no power here",
        "ok": False,
        "status_code": 403,
    }


async def test_groupless_user_cannot_create_transfer(
    client: AsyncClient,
    simple_user: MockUser,
    two_group_connections: tuple[MockConnection, MockConnection],
    session: AsyncSession,
):
    # Arrange
    first_conn, second_conn = two_group_connections

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "group_id": first_conn.owner_group.group.id,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.id,
            "target_connection_id": second_conn.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
        },
    )

    # Assert
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }


async def test_other_group_user_plus_cannot_create_group_transfer(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    session: AsyncSession,
    group: MockGroup,
    role_user_plus: TestUserRoles,
):
    # Arrange
    first_conn, second_conn = two_group_connections
    user = group.get_member_of_role(role_user_plus)

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": first_conn.owner_group.id,
            "name": "new test group transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.id,
            "target_connection_id": second_conn.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
        },
    )
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }


async def test_superuser_can_create_transfer(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    session: AsyncSession,
    superuser: MockUser,
):
    # Arrange
    first_conn, second_conn = two_group_connections

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "group_id": first_conn.owner_group.id,
            "name": "new test group transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.id,
            "target_connection_id": second_conn.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
        },
    )
    transfer = (
        await session.scalars(
            select(Transfer).filter_by(
                name="new test group transfer",
                group_id=first_conn.owner_group.id,
            )
        )
    ).one()

    assert result.status_code == 200
    assert result.json() == {
        "id": transfer.id,
        "group_id": transfer.group_id,
        "name": transfer.name,
        "description": transfer.description,
        "schedule": transfer.schedule,
        "is_scheduled": transfer.is_scheduled,
        "source_connection_id": transfer.source_connection_id,
        "target_connection_id": transfer.target_connection_id,
        "source_params": transfer.source_params,
        "target_params": transfer.target_params,
        "strategy_params": transfer.strategy_params,
    }


@pytest.mark.parametrize(
    argnames=["new_data", "error_json"],
    argvalues=(
        (
            {"is_scheduled": 2},
            {
                "loc": ["body", "is_scheduled"],
                "msg": "value could not be parsed to a boolean",
                "type": "type_error.bool",
            },
        ),
        (
            {"schedule": None},
            {
                "loc": ["body", "__root__"],
                "msg": "If transfer must be scheduled than set schedule param",
                "type": "value_error",
            },
        ),
        (
            {
                "strategy_params": {"type": "new some strategy type"},
            },
            {
                "loc": ["body", "strategy_params"],
                "msg": "No match for discriminator 'type' and value 'new some strategy type' (allowed values: 'full', 'incremental')",
                "type": "value_error.discriminated_union.invalid_discriminator",
                "ctx": {
                    "discriminator_key": "type",
                    "discriminator_value": "new some strategy type",
                    "allowed_values": "'full', 'incremental'",
                },
            },
        ),
        (
            {
                "source_params": {
                    "type": "new some connection type",
                    "table_name": "source_table",
                },
            },
            {
                "loc": ["body", "source_params"],
                "msg": "No match for discriminator 'type' and value 'new some connection type' (allowed values: 'postgres', 'oracle', 'hive')",
                "type": "value_error.discriminated_union.invalid_discriminator",
                "ctx": {
                    "discriminator_key": "type",
                    "discriminator_value": "new some connection type",
                    "allowed_values": "'postgres', 'oracle', 'hive'",
                },
            },
        ),
    ),
)
async def test_check_fields_validation_on_create_transfer(
    new_data: dict,
    error_json: dict,
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    session: AsyncSession,
    role_user_plus: TestUserRoles,
):
    # Arrange
    first_conn, second_conn = two_group_connections
    user = first_conn.owner_group.get_member_of_role(role_user_plus)

    # Act
    transfer_data = {
        "name": "new test transfer",
        "group_id": first_conn.owner_group.group.id,
        "description": "",
        "is_scheduled": True,
        "schedule": "",
        "source_connection_id": first_conn.id,
        "target_connection_id": second_conn.id,
        "source_params": {"type": "postgres", "table_name": "source_table"},
        "target_params": {"type": "postgres", "table_name": "target_table"},
        "strategy_params": {"type": "full"},
    }
    transfer_data.update(new_data)
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json=transfer_data,
    )

    # Assert
    assert result.status_code == 422
    assert result.json() == {"detail": [error_json]}


async def test_check_connection_types_and_its_params_on_create_transfer(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    session: AsyncSession,
    role_user_plus: TestUserRoles,
):
    # Arrange
    first_conn, second_conn = two_group_connections
    user = first_conn.owner_group.get_member_of_role(role_user_plus)

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "new test transfer",
            "group_id": first_conn.owner_group.group.id,
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.connection.id,
            "target_connection_id": second_conn.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "oracle", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
        },
    )

    # Assert
    assert result.status_code == 400
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "Target connection has type `postgres` but its params has `oracle` type",
    }


async def test_check_different_connections_owner_group_on_create_transfer(
    client: AsyncClient,
    session: AsyncSession,
    two_group_connections: tuple[MockConnection, MockConnection],
    group_connection: MockConnection,
    role_user_plus: TestUserRoles,
):
    # Arrange
    first_conn, _ = two_group_connections
    user = first_conn.owner_group.get_member_of_role(role_user_plus)

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "new test transfer",
            "group_id": first_conn.owner_group.group.id,
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.connection.id,
            "target_connection_id": group_connection.connection.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
        },
    )

    # Assert
    assert result.json() == {
        "message": "Connections should belong to the transfer group",
        "ok": False,
        "status_code": 400,
    }
    assert result.status_code == 400


async def test_unauthorized_user_cannot_create_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    # Act
    result = await client.post(
        "v1/transfers",
        json={
            "group_id": group_transfer.owner_group.group.id,
            "name": "New transfer name",
            "source_connection_id": group_transfer.source_connection_id,
            "target_connection_id": group_transfer.target_connection_id,
            "source_params": {"type": "postgres", "table_name": "test"},
            "target_params": {"type": "postgres", "table_name": "test1"},
        },
    )

    # Assert
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


@pytest.mark.parametrize("iter_conn_id", [(False, True), (True, False)])
async def test_group_member_cannot_create_transfer_with_unknown_connection_error(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    session: AsyncSession,
    role_user_plus: TestUserRoles,
    iter_conn_id: tuple,
):
    # Arrange
    first_conn, second_conn = two_group_connections
    user = first_conn.owner_group.get_member_of_role(role_user_plus)

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": first_conn.owner_group.group.id,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.id if iter_conn_id[0] else -1,
            "target_connection_id": second_conn.id if iter_conn_id[1] else -1,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
        },
    )

    # Assert
    assert result.json() == {
        "message": "Connection not found",
        "ok": False,
        "status_code": 404,
    }


async def test_group_member_cannot_create_transfer_with_unknown_group_error(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    session: AsyncSession,
    role_user_plus: TestUserRoles,
):
    # Arrange
    first_conn, second_conn = two_group_connections
    user = first_conn.owner_group.get_member_of_role(role_user_plus)

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": -1,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.id,
            "target_connection_id": second_conn.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
        },
    )

    # Assert

    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }


@pytest.mark.parametrize("conn_id", [(False, True), (True, False)])
async def test_superuser_cannot_create_transfer_with_unknown_connection_error(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    session: AsyncSession,
    conn_id: tuple,
    superuser: MockUser,
):
    # Arrange
    first_conn, second_conn = two_group_connections

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "group_id": first_conn.owner_group.group.id,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.id if conn_id[0] else -1,
            "target_connection_id": second_conn.id if conn_id[1] else -1,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
        },
    )

    # Assert
    assert result.json() == {
        "message": "Connection not found",
        "ok": False,
        "status_code": 404,
    }


async def test_superuser_cannot_create_transfer_with_unknown_group_error(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    session: AsyncSession,
    superuser: MockUser,
):
    # Arrange
    first_conn, second_conn = two_group_connections

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "group_id": -1,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.id,
            "target_connection_id": second_conn.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
        },
    )

    # Assert
    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }
