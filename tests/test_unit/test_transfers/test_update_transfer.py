import pytest
from httpx import AsyncClient

from syncmaster.db.models import Queue
from tests.mocks import MockConnection, MockGroup, MockTransfer, MockUser, UserTestRoles
from tests.test_unit.utils import build_transfer_json, fetch_transfer_json

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_developer_plus_can_update_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_developer_plus: UserTestRoles,
):
    user = group_transfer.owner_group.get_member_of_role(role_developer_plus)
    transfer_json = await fetch_transfer_json(client, user.token, group_transfer)
    updated_fields = {
        "name": "New transfer name",
        "is_scheduled": False,
        "strategy_params": {
            "type": "incremental",
            "increment_by": "updated_at",
        },
        "resources": {
            "max_parallel_tasks": 5,
            "cpu_cores_per_task": 4,
            "ram_bytes_per_task": 2 * 1024**3,
        },
    }

    result = await client.put(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json=transfer_json | updated_fields,
    )

    assert result.status_code == 200, result.json()
    assert result.json() == build_transfer_json(group_transfer) | updated_fields


async def test_groupless_user_cannot_update_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    simple_user: MockUser,
):
    transfer_json = build_transfer_json(group_transfer)
    result = await client.put(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={**transfer_json, "name": "New transfer name"},
    )

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }


async def test_superuser_can_update_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    superuser: MockUser,
):
    updated_fields = {"name": "New transfer name"}
    transfer_json = await fetch_transfer_json(client, superuser.token, group_transfer)

    result = await client.put(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json=transfer_json | updated_fields,
    )

    assert result.status_code == 200, result.json()
    assert result.json() == build_transfer_json(group_transfer) | updated_fields


async def test_other_group_member_cannot_update_transfer(
    client: AsyncClient,
    group: MockGroup,
    group_transfer: MockTransfer,
    role_developer_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_developer_plus)
    transfer_json = build_transfer_json(group_transfer)

    result = await client.put(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json=transfer_json,
    )

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }


async def test_check_name_field_validation_on_update_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_developer_plus: UserTestRoles,
):
    user = group_transfer.owner_group.get_member_of_role(role_developer_plus)
    transfer_json = await fetch_transfer_json(client, user.token, group_transfer)

    result = await client.put(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={**transfer_json, "name": ""},
    )

    assert result.status_code == 422, result.json()
    assert result.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [
                {
                    "context": {"min_length": 1},
                    "input": "",
                    "location": ["body", "name"],
                    "message": "String should have at least 1 character",
                    "code": "string_too_short",
                },
            ],
        },
    }


async def test_check_connection_types_and_its_params_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_developer_plus: UserTestRoles,
):
    user = group_transfer.owner_group.get_member_of_role(role_developer_plus)
    transfer_json = await fetch_transfer_json(client, user.token, group_transfer)
    updated_fields = {
        "name": "New transfer name",
        "source_params": {
            "type": "oracle",
            "table_name": "New table name",
        },
    }

    result = await client.put(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json=transfer_json | updated_fields,
    )

    assert result.status_code == 400, result.json()
    assert result.json() == {
        "error": {
            "code": "bad_request",
            "message": "Source connection has type `postgres` but its params has `oracle` type",
            "details": None,
        },
    }

    updated_fields["source_params"]["type"] = "postgres"
    result = await client.put(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json=transfer_json | updated_fields,
    )

    assert result.status_code == 200, result.json()
    assert result.json() == build_transfer_json(group_transfer) | updated_fields


async def test_check_different_connection_groups_for_transfer(
    client: AsyncClient,
    group_transfer_and_group_connection_developer_plus,
    group_transfer: MockTransfer,
):
    role, connection = group_transfer_and_group_connection_developer_plus
    user = group_transfer.owner_group.get_member_of_role(role)
    transfer_json = await fetch_transfer_json(client, user.token, group_transfer)

    result = await client.put(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={**transfer_json, "source_connection_id": connection.id},
    )

    assert result.status_code == 400, result.json()
    assert result.json() == {
        "error": {
            "code": "bad_request",
            "message": "Connections should belong to the transfer group",
            "details": None,
        },
    }


async def test_check_different_queue_groups_for_transfer(
    client: AsyncClient,
    group_queue: Queue,
    group_transfer: MockTransfer,
    role_developer_plus: UserTestRoles,
):
    user = group_transfer.owner_group.get_member_of_role(role_developer_plus)
    transfer_json = await fetch_transfer_json(client, user.token, group_transfer)

    result = await client.put(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={**transfer_json, "queue_id": group_queue.id},
    )

    assert result.status_code == 400, result.json()
    assert result.json() == {
        "error": {
            "code": "bad_request",
            "message": "Queue should belong to the transfer group",
            "details": None,
        },
    }


async def test_developer_plus_not_in_new_connection_group_cannot_update_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    user = group_transfer.owner_group.get_member_of_role(role_developer_plus)
    transfer_json = await fetch_transfer_json(client, user.token, group_transfer)

    result = await client.put(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={**transfer_json, "source_connection_id": group_connection.connection.id},
    )

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }


async def test_unauthorized_user_cannot_update_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    transfer_json = build_transfer_json(group_transfer)

    result = await client.put(
        f"v1/transfers/{group_transfer.id}",
        json={**transfer_json, "name": "New transfer name"},
    )

    assert result.status_code == 401, result.json()
    assert result.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_developer_plus_cannot_update_transfer_with_other_group_queue(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_developer_plus: UserTestRoles,
    group_queue: Queue,
):
    user = group_transfer.owner_group.get_member_of_role(role_developer_plus)
    transfer_json = await fetch_transfer_json(client, user.token, group_transfer)

    result = await client.put(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={**transfer_json, "queue_id": group_queue.id},
    )

    assert result.status_code == 400, result.json()
    assert result.json() == {
        "error": {
            "code": "bad_request",
            "message": "Queue should belong to the transfer group",
            "details": None,
        },
    }


async def test_superuser_cannot_update_transfer_with_other_group_queue(
    client: AsyncClient,
    group_transfer: MockTransfer,
    superuser: MockUser,
    group_queue: Queue,
):
    transfer_json = await fetch_transfer_json(client, superuser.token, group_transfer)

    result = await client.put(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={**transfer_json, "queue_id": group_queue.id},
    )

    assert result.status_code == 400, result.json()
    assert result.json() == {
        "error": {
            "code": "bad_request",
            "message": "Queue should belong to the transfer group",
            "details": None,
        },
    }


async def test_group_member_cannot_update_unknown_transfer_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_guest_plus: UserTestRoles,
):
    user = group_transfer.owner_group.get_member_of_role(role_guest_plus)
    transfer_json = await fetch_transfer_json(client, user.token, group_transfer)

    result = await client.put(
        "v1/transfers/-1",
        headers={"Authorization": f"Bearer {user.token}"},
        json={**transfer_json, "name": "New transfer name"},
    )

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }


async def test_superuser_cannot_update_unknown_transfer_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    superuser: MockUser,
):
    transfer_json = await fetch_transfer_json(client, superuser.token, group_transfer)

    result = await client.put(
        "v1/transfers/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={**transfer_json, "name": "New transfer name"},
    )

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }


async def test_developer_plus_cannot_update_transfer_with_unknown_queue_id_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_developer_plus: UserTestRoles,
):
    user = group_transfer.owner_group.get_member_of_role(role_developer_plus)
    transfer_json = await fetch_transfer_json(client, user.token, group_transfer)

    result = await client.put(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={**transfer_json, "queue_id": -1},
    )

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Queue not found",
            "details": None,
        },
    }


async def test_superuser_cannot_update_transfer_with_unknown_queue_id(
    client: AsyncClient,
    group_transfer: MockTransfer,
    superuser: MockUser,
):
    transfer_json = await fetch_transfer_json(client, superuser.token, group_transfer)

    result = await client.put(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={**transfer_json, "queue_id": -1},
    )

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Queue not found",
            "details": None,
        },
    }
