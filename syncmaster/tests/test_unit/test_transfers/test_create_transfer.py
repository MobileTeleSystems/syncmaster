import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_unit.utils import create_connection
from tests.utils import MockConnection, MockGroup, MockTransfer, MockUser

from app.db.models import Transfer

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_create_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    result = await client.post(
        "v1/transfers",
        json={
            "group_id": None,
            "name": "New transfer",
            "source_connection_id": group_transfer.source_connection_id,
            "target_connection_id": group_transfer.target_connection_id,
            "source_params": {"type": "postgres", "table_name": "test"},
            "target_params": {"type": "postgres", "table_name": "test1"},
        },
    )
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_group_member_can_create_transfer(
    client: AsyncClient,
    group_connection: MockConnection,
    session: AsyncSession,
):
    user = group_connection.owner_group.members[0]
    other_connection = await create_connection(
        session=session,
        name="other_connection",
        group_id=group_connection.owner_group.group.id,
    )

    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group_connection.owner_group.group.id,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": group_connection.id,
            "target_connection_id": other_connection.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
        },
    )
    transfer = (
        await session.scalars(
            select(Transfer).filter_by(
                name="new test transfer",
                group_id=group_connection.owner_group.group.id,
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

    await session.delete(other_connection)
    await session.commit()


async def test_groupless_user_cannot_create_transfer(
    client: AsyncClient,
    simple_user: MockUser,
    group_connection: MockConnection,
    session: AsyncSession,
):
    other_connection = await create_connection(
        session=session,
        name="other_connection",
        group_id=group_connection.owner_group.group.id,
    )
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "group_id": group_connection.owner_group.group.id,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": group_connection.id,
            "target_connection_id": other_connection.id,
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

    await session.delete(other_connection)
    await session.commit()


async def test_other_group_admin_cannot_create_group_transfer(
    client: AsyncClient,
    group_connection: MockConnection,
    session: AsyncSession,
    empty_group: MockGroup,
):
    other_admin = empty_group.admin
    other_connection = await create_connection(
        session=session,
        name="other_connection",
        group_id=group_connection.owner_group.id,
    )
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {other_admin.token}"},
        json={
            "group_id": group_connection.owner_group.id,
            "name": "new test group transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": group_connection.id,
            "target_connection_id": other_connection.id,
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


async def test_group_admin_can_create_own_group_transfer(
    client: AsyncClient,
    group_connection: MockConnection,
    session: AsyncSession,
):
    admin = group_connection.owner_group.admin
    other_connection = await create_connection(
        session=session,
        name="other_connection",
        group_id=group_connection.owner_group.id,
    )
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={
            "group_id": group_connection.owner_group.id,
            "name": "new test group transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": group_connection.id,
            "target_connection_id": other_connection.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
        },
    )
    transfer = (
        await session.scalars(
            select(Transfer).filter_by(
                name="new test group transfer",
                group_id=group_connection.owner_group.id,
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

    await session.delete(other_connection)
    await session.commit()


async def test_superuser_can_create_transfer(
    client: AsyncClient,
    group_connection: MockConnection,
    session: AsyncSession,
    superuser: MockUser,
):
    other_connection = await create_connection(
        session=session,
        name="other_connection",
        group_id=group_connection.owner_group.id,
    )
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "group_id": group_connection.owner_group.id,
            "name": "new test group transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": group_connection.id,
            "target_connection_id": other_connection.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
        },
    )
    transfer = (
        await session.scalars(
            select(Transfer).filter_by(
                name="new test group transfer",
                group_id=group_connection.owner_group.id,
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

    await session.delete(other_connection)
    await session.commit()


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
    group_connection: MockConnection,
    session: AsyncSession,
):
    admin_user = group_connection.owner_group.admin

    other_connection = await create_connection(
        session=session,
        name="other_connection",
        group_id=group_connection.owner_group.group.id,
    )

    transfer_data = {
        "name": "new test transfer",
        "group_id": group_connection.owner_group.group.id,
        "description": "",
        "is_scheduled": True,
        "schedule": "",
        "source_connection_id": group_connection.id,
        "target_connection_id": other_connection.id,
        "source_params": {"type": "postgres", "table_name": "source_table"},
        "target_params": {"type": "postgres", "table_name": "target_table"},
        "strategy_params": {"type": "full"},
    }
    transfer_data.update(new_data)
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {admin_user.token}"},
        json=transfer_data,
    )
    assert result.status_code == 422
    assert result.json() == {"detail": [error_json]}


async def test_check_connection_types_and_its_params_on_create_transfer(
    client: AsyncClient,
    group_connection: MockConnection,
    session: AsyncSession,
):
    admin_user = group_connection.owner_group.admin

    other_connection = await create_connection(
        session=session,
        name="other_connection",
        group_id=group_connection.owner_group.group.id,
    )

    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {admin_user.token}"},
        json={
            "name": "new test transfer",
            "group_id": group_connection.owner_group.group.id,
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": group_connection.connection.id,
            "target_connection_id": other_connection.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "oracle", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
        },
    )
    assert result.status_code == 400
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "Target connection has type `postgres` but its params has `oracle` type",
    }

    await session.delete(other_connection)
    await session.commit()


async def test_check_different_connection_owners_on_create_transfer(
    client: AsyncClient,
    group_connection: MockConnection,
    empty_group: MockConnection,
    session: AsyncSession,
):
    # Arrange
    user = group_connection.owner_group.members[0]

    await client.post(
        f"v1/groups/{empty_group.id}/users/{user.user.id}",
        headers={"Authorization": f"Bearer {empty_group.admin.token}"},
    )

    new_connection = await create_connection(
        session=session,
        name="New group admin connection",
        group_id=empty_group.id,
    )
    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "new test transfer",
            "group_id": group_connection.owner_group.group.id,
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": group_connection.id,
            "target_connection_id": new_connection.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
        },
    )

    # Assert
    assert result.status_code == 400
    assert result.json() == {
        "message": "Connections should belong to the transfer group",
        "ok": False,
        "status_code": 400,
    }
    await session.delete(new_connection)
    await session.commit()


async def test_group_member_can_not_create_transfer_with_another_group_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    empty_group: MockConnection,
    session: AsyncSession,
):
    # Arrange
    admin = group_connection.owner_group.admin
    new_connection = await create_connection(
        session=session,
        name="New group admin connection",
        group_id=empty_group.id,
    )

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={
            "name": "new test transfer",
            "group_id": group_connection.owner_group.group.id,
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": group_connection.id,
            "target_connection_id": new_connection.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
        },
    )

    # Assert
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }
    await session.delete(new_connection)
    await session.commit()
