import random
import string

import pytest
from httpx import AsyncClient

from tests.mocks import MockTransfer, MockUser, UserTestRoles
from tests.test_unit.utils import build_transfer_json

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_guest_plus_can_read_transfers(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_guest_plus: UserTestRoles,
):
    user = group_transfer.owner_group.get_member_of_role(role_guest_plus)

    response = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        params={"group_id": group_transfer.owner_group.group.id},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
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
            build_transfer_json(group_transfer),
        ],
    }


async def test_groupless_user_cannot_read_transfers(
    client: AsyncClient,
    simple_user: MockUser,
    group_transfer: MockTransfer,
):
    response = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        params={"group_id": group_transfer.owner_group.group.id},
    )

    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_superuser_can_read_transfers(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
):
    response = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"group_id": group_transfer.owner_group.group.id},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
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
            build_transfer_json(group_transfer),
        ],
    }


@pytest.mark.parametrize(
    "search_value_extractor",
    [
        lambda transfer: transfer.name,
        lambda transfer: transfer.source_params.get("table_name"),
        lambda transfer: transfer.target_params.get("table_name"),
        lambda transfer: transfer.source_params.get("directory_path"),
        lambda transfer: transfer.target_params.get("directory_path"),
    ],
    ids=[
        "name",
        "source_table_name",
        "target_table_name",
        "source_directory_path",
        "target_directory_path",
    ],
)
async def test_search_transfers_with_query(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
    search_value_extractor,
):
    transfer = group_transfer.transfer
    search_query = search_value_extractor(transfer)

    response = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"group_id": group_transfer.group_id, "search_query": search_query},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
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
            build_transfer_json(group_transfer),
        ],
    }


async def test_search_transfers_with_nonexistent_query(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
):
    random_search_query = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))

    response = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={
            "group_id": group_transfer.group_id,
            "search_query": random_search_query,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["items"] == []


@pytest.mark.parametrize(
    ["filter_param", "get_filter_value"],
    [
        ("source_connection_id", lambda t: t.source_connection_id),
        ("target_connection_id", lambda t: t.target_connection_id),
        ("queue_id", lambda t: t.queue_id),
        ("is_scheduled", lambda t: t.is_scheduled),
    ],
    ids=["source_connection_id", "target_connection_id", "queue_id", "is_scheduled"],
)
async def test_filter_transfers(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
    filter_param,
    get_filter_value,
):
    transfer = group_transfer.transfer
    group_id = transfer.group_id

    filter_value = get_filter_value(transfer)

    params = {
        "group_id": group_id,
        filter_param: filter_value,
    }
    response = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params=params,
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
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
            build_transfer_json(group_transfer),
        ],
    }


@pytest.mark.parametrize(
    ["filter_param", "get_non_matching_value"],
    [
        ("source_connection_id", lambda t: -1),
        ("target_connection_id", lambda t: -1),
        ("queue_id", lambda t: -1),
        ("is_scheduled", lambda t: not t.is_scheduled),
    ],
    ids=["source_connection_id", "target_connection_id", "queue_id", "is_scheduled"],
)
async def test_filter_transfers_no_responses(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
    filter_param,
    get_non_matching_value,
):
    transfer = group_transfer.transfer
    group_id = transfer.group_id

    non_matching_value = get_non_matching_value(transfer)

    params = {
        "group_id": group_id,
        filter_param: non_matching_value,
    }
    response = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params=params,
    )

    assert response.status_code == 200, response.text
    assert response.json()["items"] == []


@pytest.mark.parametrize(
    ["filter_param", "connection_type"],
    [
        ("source_connection_type", "postgres"),
        ("target_connection_type", "oracle"),
        ("source_connection_type", "hive"),
        ("target_connection_type", "s3"),
    ],
    ids=[
        "source_connection_type_postgres",
        "target_connection_type_oracle",
        "source_connection_type_hive",
        "target_connection_type_s3",
    ],
)
async def test_filter_transfers_with_multiple_transfers(
    client: AsyncClient,
    superuser: MockUser,
    group_transfers: list[MockTransfer],
    filter_param,
    connection_type,
):
    group_id = group_transfers[0].group_id

    params = {
        "group_id": group_id,
        filter_param: [connection_type],
    }
    response = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params=params,
    )
    expected_transfers = []
    for transfer in group_transfers:
        connection_type_value = None
        if filter_param == "source_connection_type":
            connection_type_value = transfer.source_connection.connection.type
        elif filter_param == "target_connection_type":
            connection_type_value = transfer.target_connection.connection.type
        if connection_type_value == connection_type:
            expected_transfers.append(transfer)

    assert response.status_code == 200, response.text
    expected_items = [build_transfer_json(t) for t in expected_transfers]
    assert response.json()["items"] == expected_items


async def test_unauthorized_user_cannot_read_transfers(client: AsyncClient):
    response = await client.get("v1/transfers")

    assert response.status_code == 401, response.text
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_developer_plus_cannot_read_unknown_group_transfers_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_developer_plus: UserTestRoles,
):
    user = group_transfer.owner_group.get_member_of_role(role_developer_plus)

    response = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        params={"group_id": -1},
    )

    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_superuser_cannot_read_unknown_group_transfers_error(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
):
    response = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"group_id": -1},
    )

    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
