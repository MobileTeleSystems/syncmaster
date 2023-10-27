import pytest
from httpx import AsyncClient
from tests.utils import MockTransfer, MockUser

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_read_transfers(client: AsyncClient):
    result = await client.get("v1/transfers")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_user_can_read_own_transfers(
    client: AsyncClient,
    simple_user: MockUser,
    user_transfer: MockTransfer,
):
    result = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 0,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [],
    }

    result = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user_transfer.owner_user.token}"},
    )
    assert result.status_code == 200
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
                "id": user_transfer.id,
                "user_id": user_transfer.user_id,
                "group_id": user_transfer.group_id,
                "name": user_transfer.name,
                "description": user_transfer.description,
                "schedule": user_transfer.schedule,
                "is_scheduled": user_transfer.is_scheduled,
                "source_connection_id": user_transfer.source_connection_id,
                "target_connection_id": user_transfer.target_connection_id,
                "source_params": user_transfer.source_params,
                "target_params": user_transfer.target_params,
                "strategy_params": user_transfer.strategy_params,
            }
        ],
    }


async def test_group_admin_can_read_transfers(
    client: AsyncClient,
    simple_user: MockUser,
    group_transfer: MockTransfer,
):
    result = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 0,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [],
    }

    admin = group_transfer.owner_group.admin
    result = await client.get(
        "v1/transfers",
        headers={"Authorization": f"Bearer {admin.token}"},
    )
    assert result.status_code == 200
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
                "user_id": group_transfer.user_id,
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
            }
        ],
    }


async def test_group_member_can_read_tranfers(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    result = await client.get(
        "v1/transfers",
        headers={
            "Authorization": f"Bearer {group_transfer.owner_group.members[0].token}"
        },
    )
    assert result.status_code == 200
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
                "user_id": group_transfer.user_id,
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
            }
        ],
    }


async def test_superuser_can_read_all_transfers(
    client: AsyncClient,
    superuser: MockUser,
    user_transfer: MockTransfer,
    group_transfer: MockTransfer,
):
    result = await client.get(
        "v1/transfers", headers={"Authorization": f"Bearer {superuser.token}"}
    )
    assert result.status_code == 200
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 2,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [
            {
                "id": group_transfer.id,
                "user_id": group_transfer.user_id,
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
            },
            {
                "id": user_transfer.id,
                "user_id": user_transfer.user_id,
                "group_id": user_transfer.group_id,
                "name": user_transfer.name,
                "description": user_transfer.description,
                "schedule": user_transfer.schedule,
                "is_scheduled": user_transfer.is_scheduled,
                "source_connection_id": user_transfer.source_connection_id,
                "target_connection_id": user_transfer.target_connection_id,
                "source_params": user_transfer.source_params,
                "target_params": user_transfer.target_params,
                "strategy_params": user_transfer.strategy_params,
            },
        ],
    }
