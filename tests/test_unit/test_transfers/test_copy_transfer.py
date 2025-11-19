import secrets
from operator import or_

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Connection, Queue, Transfer
from syncmaster.db.models.auth_data import AuthData
from tests.mocks import MockGroup, MockTransfer, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_maintainer_plus_can_copy_transfer_with_remove_source(
    client: AsyncClient,
    session: AsyncSession,
    request,
    event_loop,
    group_transfer_and_group_maintainer_plus: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    role = group_transfer_and_group_maintainer_plus
    user = group_transfer.owner_group.get_member_of_role(role)

    old_transfer = await session.get(Transfer, group_transfer.id)

    new_transfer_query = select(Transfer).filter(
        Transfer.group_id == group_queue.group_id,
        Transfer.name == group_transfer.name,
    )
    new_transfer = (await session.scalars(new_transfer_query)).one_or_none()
    assert not new_transfer

    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
            "remove_source": True,
        },
    )

    assert result.status_code == 200, result.json()

    # new transfer exist in target group
    new_transfer = (await session.scalars(new_transfer_query)).one()

    assert result.json() == {
        "id": new_transfer.id,
        "group_id": group_queue.group_id,
        "queue_id": group_queue.id,
        "source_connection_id": new_transfer.source_connection_id,
        "target_connection_id": new_transfer.target_connection_id,
        "name": old_transfer.name,
        "description": old_transfer.description,
        "schedule": old_transfer.schedule,
        "is_scheduled": old_transfer.is_scheduled,
        "source_params": old_transfer.source_params,
        "target_params": old_transfer.target_params,
        "strategy_params": old_transfer.strategy_params,
        "transformations": old_transfer.transformations,
        "resources": old_transfer.resources,
    }

    def delete_rows():
        async def afin():
            delete_new_connections_query = delete(Connection).where(
                or_(
                    Connection.id == new_transfer.source_connection_id,
                    Connection.id == new_transfer.target_connection_id,
                ),
            )
            await session.execute(delete_new_connections_query)
            await session.commit()

        event_loop.run_until_complete(afin())

    request.addfinalizer(delete_rows)

    # New connections were created
    new_source_connection = await session.get(Connection, new_transfer.source_connection_id)
    new_target_connection = await session.get(Connection, new_transfer.target_connection_id)
    assert new_source_connection is not None
    assert new_target_connection is not None

    # Auth data for new connections was reset
    new_source_auth_data = await session.get(AuthData, new_source_connection.id)
    new_target_auth_data = await session.get(AuthData, new_target_connection.id)
    assert new_source_auth_data is None
    assert new_target_auth_data is None

    # Check old (original) transfer was deleted
    session.expunge(old_transfer)
    old_transfer = await session.get(Transfer, old_transfer.id)
    assert old_transfer is None


async def test_maintainer_plus_can_copy_transfer_with_new_name(
    client: AsyncClient,
    session: AsyncSession,
    event_loop,
    group_transfer_and_group_maintainer_plus: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
    request,
):
    role = group_transfer_and_group_maintainer_plus
    user = group_transfer.owner_group.get_member_of_role(role)
    new_name = f"{secrets.token_hex(5)}"

    old_transfer = await session.get(Transfer, group_transfer.id)

    new_transfer_query = select(Transfer).filter(
        Transfer.group_id == group_queue.group_id,
        Transfer.name == new_name,
    )
    new_transfer = (await session.scalars(new_transfer_query)).one_or_none()
    assert not new_transfer

    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
            "new_name": new_name,
        },
    )

    assert result.status_code == 200, result.json()

    # new transfer with new name exist in target group
    new_transfer = (await session.scalars(new_transfer_query)).one()

    assert result.json() == {
        "id": new_transfer.id,
        "group_id": group_queue.group_id,
        "queue_id": group_queue.id,
        "source_connection_id": new_transfer.source_connection_id,
        "target_connection_id": new_transfer.target_connection_id,
        "name": new_name,
        "description": old_transfer.description,
        "schedule": old_transfer.schedule,
        "is_scheduled": old_transfer.is_scheduled,
        "source_params": old_transfer.source_params,
        "target_params": old_transfer.target_params,
        "strategy_params": old_transfer.strategy_params,
        "transformations": old_transfer.transformations,
        "resources": old_transfer.resources,
    }

    def delete_rows():
        async def afin():
            delete_new_connections_query = delete(Connection).where(
                or_(
                    Connection.id == new_transfer.source_connection_id,
                    Connection.id == new_transfer.target_connection_id,
                ),
            )
            await session.execute(delete_new_connections_query)
            await session.commit()

        event_loop.run_until_complete(afin())

    request.addfinalizer(delete_rows)

    # New connections were created
    new_source_connection = await session.get(Connection, new_transfer.source_connection_id)
    new_target_connection = await session.get(Connection, new_transfer.target_connection_id)
    assert new_source_connection is not None
    assert new_target_connection is not None

    # Auth data for new connections was reset
    new_source_auth_data = await session.get(AuthData, new_source_connection.id)
    new_target_auth_data = await session.get(AuthData, new_target_connection.id)
    assert new_source_auth_data is None
    assert new_target_auth_data is None

    # Check old (original) transfer still exists
    session.expunge(old_transfer)
    old_transfer = await session.get(Transfer, old_transfer.id)
    assert old_transfer is not None


async def test_developer_plus_can_copy_transfer_without_remove_source(
    client: AsyncClient,
    session: AsyncSession,
    request,
    event_loop,
    group_transfer_and_group_developer_plus: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    role = group_transfer_and_group_developer_plus
    user = group_transfer.owner_group.get_member_of_role(role)

    old_transfer = await session.get(Transfer, group_transfer.id)

    new_transfer_query = select(Transfer).filter(
        Transfer.group_id == group_queue.group_id,
        Transfer.name == group_transfer.name,
    )
    new_transfer = (await session.scalars(new_transfer_query)).one_or_none()
    assert not new_transfer

    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
            "remove_source": False,
        },
    )

    assert result.status_code == 200, result.json()

    # new transfer exist in target group
    new_transfer = (await session.scalars(new_transfer_query)).one()

    assert result.json() == {
        "id": new_transfer.id,
        "group_id": group_queue.group_id,
        "queue_id": group_queue.id,
        "source_connection_id": new_transfer.source_connection_id,
        "target_connection_id": new_transfer.target_connection_id,
        "name": old_transfer.name,
        "description": old_transfer.description,
        "schedule": old_transfer.schedule,
        "is_scheduled": old_transfer.is_scheduled,
        "source_params": old_transfer.source_params,
        "target_params": old_transfer.target_params,
        "strategy_params": old_transfer.strategy_params,
        "transformations": old_transfer.transformations,
        "resources": old_transfer.resources,
    }

    def delete_rows():
        async def afin():
            delete_new_connections_query = delete(Connection).where(
                or_(
                    Connection.id == new_transfer.source_connection_id,
                    Connection.id == new_transfer.target_connection_id,
                ),
            )
            await session.execute(delete_new_connections_query)
            await session.commit()

        event_loop.run_until_complete(afin())

    request.addfinalizer(delete_rows)

    # New connections were created
    new_source_connection = await session.get(Connection, new_transfer.source_connection_id)
    new_target_connection = await session.get(Connection, new_transfer.target_connection_id)
    assert new_source_connection is not None
    assert new_target_connection is not None

    # Auth data for new connections was reset
    new_source_auth_data = await session.get(AuthData, new_source_connection.id)
    new_target_auth_data = await session.get(AuthData, new_target_connection.id)
    assert new_source_auth_data is None
    assert new_target_auth_data is None

    # Check old (original) transfer still exists
    session.expunge(old_transfer)
    old_transfer = await session.get(Transfer, old_transfer.id)
    assert old_transfer is not None


async def test_developer_or_below_cannot_copy_transfer_with_remove_source(
    client: AsyncClient,
    group_transfer_and_group_developer_or_below: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    role = group_transfer_and_group_developer_or_below
    user = group_transfer.owner_group.get_member_of_role(role)

    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
            "remove_source": True,
        },
    )

    assert result.status_code == 403, result.json()
    assert result.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }


async def test_superuser_can_copy_transfer_with_remove_source(
    client: AsyncClient,
    session: AsyncSession,
    request,
    event_loop,
    superuser: MockUser,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    old_transfer = await session.get(Transfer, group_transfer.id)

    new_transfer_query = select(Transfer).filter(
        Transfer.group_id == group_queue.group_id,
        Transfer.name == group_transfer.name,
    )
    new_transfer = (await session.scalars(new_transfer_query)).one_or_none()
    assert not new_transfer

    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
            "remove_source": True,
        },
    )

    assert result.status_code == 200, result.json()

    # new transfer exist in target group
    new_transfer = (await session.scalars(new_transfer_query)).one()

    assert result.json() == {
        "id": new_transfer.id,
        "group_id": group_queue.group_id,
        "queue_id": group_queue.id,
        "source_connection_id": new_transfer.source_connection_id,
        "target_connection_id": new_transfer.target_connection_id,
        "name": old_transfer.name,
        "description": old_transfer.description,
        "schedule": old_transfer.schedule,
        "is_scheduled": old_transfer.is_scheduled,
        "source_params": old_transfer.source_params,
        "target_params": old_transfer.target_params,
        "strategy_params": old_transfer.strategy_params,
        "transformations": old_transfer.transformations,
        "resources": old_transfer.resources,
    }

    def delete_rows():
        async def afin():
            delete_new_connections_query = delete(Connection).where(
                or_(
                    Connection.id == new_transfer.source_connection_id,
                    Connection.id == new_transfer.target_connection_id,
                ),
            )
            await session.execute(delete_new_connections_query)
            await session.commit()

        event_loop.run_until_complete(afin())

    request.addfinalizer(delete_rows)

    # New connections were created
    new_source_connection = await session.get(Connection, new_transfer.source_connection_id)
    new_target_connection = await session.get(Connection, new_transfer.target_connection_id)
    assert new_source_connection is not None
    assert new_target_connection is not None

    # Auth data for new connections was reset
    new_source_auth_data = await session.get(AuthData, new_source_connection.id)
    new_target_auth_data = await session.get(AuthData, new_target_connection.id)
    assert new_source_auth_data is None
    assert new_target_auth_data is None

    # Check old (original) transfer was removed
    session.expunge(old_transfer)
    old_transfer = await session.get(Transfer, old_transfer.id)
    assert old_transfer is None


async def test_maintainer_plus_can_not_copy_transfer_with_same_name_in_new_group(
    client: AsyncClient,
    group_transfer_with_same_name_maintainer_plus: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    role = group_transfer_with_same_name_maintainer_plus
    user = group_transfer.owner_group.get_member_of_role(role)
    new_name = "duplicated_group_transfer"

    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
            "new_name": new_name,
        },
    )

    assert result.json() == {
        "error": {
            "code": "conflict",
            "message": "The transfer name already exists in the target group, please specify a new one",
            "details": None,
        },
    }


@pytest.mark.parametrize(
    ("name", "error"),
    [
        pytest.param(
            "aa",
            {
                "context": {"min_length": 3},
                "input": "aa",
                "location": ["body", "new_name"],
                "message": "String should have at least 3 characters",
                "code": "string_too_short",
            },
            id="name_too_short",
        ),
        pytest.param(
            "a" * 129,
            {
                "context": {"max_length": 128},
                "input": "a" * 129,
                "location": ["body", "new_name"],
                "message": "String should have at most 128 characters",
                "code": "string_too_long",
            },
            id="name_too_long",
        ),
    ],
)
async def test_check_new_name_field_validation_on_copy_transfer(
    client: AsyncClient,
    group_transfer_and_group_maintainer_plus: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
    name: str,
    error: dict,
):
    role = group_transfer_and_group_maintainer_plus
    user = group_transfer.owner_group.get_member_of_role(role)

    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
            "new_name": name,
        },
    )

    assert result.status_code == 422, result.json()
    assert result.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [error],
        },
    }


async def test_groupless_user_cannot_copy_transfer(
    client: AsyncClient,
    simple_user: MockUser,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
        },
    )

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }


async def test_other_group_guest_plus_member_cannot_copy_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
    group_queue: Queue,
):
    user = group.get_member_of_role(role_guest_plus)

    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
        },
    )

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }


async def test_developer_plus_cannot_copy_transfer_if_new_queue_in_another_group(
    client: AsyncClient,
    group_transfer_and_group_maintainer_plus: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
    mock_queue: Queue,
):
    role = group_transfer_and_group_maintainer_plus
    user = group_transfer.owner_group.get_member_of_role(role)

    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": mock_queue.id,
        },
    )

    assert result.json() == {
        "error": {
            "code": "bad_request",
            "message": "Queue should belong to the transfer group",
            "details": None,
        },
    }
    assert result.status_code == 400, result.json()


async def test_superuser_cannot_copy_unknown_transfer_error(
    client: AsyncClient,
    superuser: MockUser,
    group_queue: Queue,
):
    result = await client.post(
        "v1/transfers/-1/copy_transfer",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "remove_source": True,
            "new_queue_id": group_queue.id,
        },
    )

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }


async def test_superuser_cannot_copy_transfer_with_unknown_new_group_error(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    result = await client.post(
        f"v1/transfers/{group_transfer.transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": -1,
            "remove_source": True,
            "new_queue_id": group_queue.id,
        },
    )

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_developer_plus_cannot_copy_transfer_with_unknown_new_group_error(
    client: AsyncClient,
    group_transfer_and_group_developer_plus: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    role = group_transfer_and_group_developer_plus
    user = group_transfer.owner_group.get_member_of_role(role)

    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": -1,
            "new_queue_id": group_queue.id,
        },
    )

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_maintainer_plus_cannot_copy_unknown_transfer_error(
    client: AsyncClient,
    group_transfer_and_group_maintainer_plus: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    role = group_transfer_and_group_maintainer_plus
    user = group_transfer.owner_group.get_member_of_role(role)

    result = await client.post(
        "v1/transfers/-1/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
        },
    )

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }


async def test_developer_plus_cannot_copy_transfer_to_unknown_queue_error(
    client: AsyncClient,
    group_transfer_and_group_developer_plus: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    role = group_transfer_and_group_developer_plus
    user = group_transfer.owner_group.get_member_of_role(role)

    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": -1,
        },
    )

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Queue not found",
            "details": None,
        },
    }


async def test_superuser_cannot_copy_transfer_with_unknown_new_queue_id_error(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": -1,
            "remove_source": True,
        },
    )

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Queue not found",
            "details": None,
        },
    }
