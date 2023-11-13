import pytest
from httpx import AsyncClient
from tests.utils import MockRun, MockTransfer, MockUser, TestUserRoles

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_read_run(
    client: AsyncClient,
    group_transfer: MockTransfer,
) -> None:
    result = await client.get(f"v1/transfers/{group_transfer.id}/runs")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_groupless_user_can_not_read_runs_transfer(
    client: AsyncClient,
    simple_user: MockUser,
    group_run: MockRun,
) -> None:
    result = await client.get(
        f"v1/transfers/{group_run.transfer.id}/runs",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }


async def test_group_admin_can_read_runs_of_the_own_transfer(
    client: AsyncClient,
    group_run: MockRun,
) -> None:
    result = await client.get(
        f"v1/transfers/{group_run.transfer.id}/runs",
        headers={
            "Authorization": f"Bearer {group_run.transfer.owner_group.get_member_of_role(TestUserRoles.Owner).token}"
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
                "id": group_run.id,
                "transfer_id": group_run.transfer_id,
                "status": group_run.status.value,
                "started_at": group_run.started_at,
                "ended_at": group_run.ended_at,
                "log_url": group_run.log_url,
            },
        ],
    }


async def test_group_member_can_read_runs_of_the_transfer(
    client: AsyncClient,
    group_run: MockRun,
) -> None:
    result = await client.get(
        f"v1/transfers/{group_run.transfer.id}/runs",
        headers={
            "Authorization": f"Bearer {group_run.transfer.owner_group.get_member_of_role(TestUserRoles.User).token}"
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
                "id": group_run.id,
                "transfer_id": group_run.transfer_id,
                "status": group_run.status.value,
                "started_at": group_run.started_at,
                "ended_at": group_run.ended_at,
                "log_url": group_run.log_url,
            },
        ],
    }


async def test_superuser_can_read_any_runs_by_id(
    client: AsyncClient,
    superuser: MockUser,
    group_run: MockRun,
) -> None:
    result = await client.get(
        f"v1/transfers/{group_run.transfer.id}/runs",
        headers={"Authorization": f"Bearer {superuser.token}"},
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
                "id": group_run.id,
                "transfer_id": group_run.transfer_id,
                "status": group_run.status.value,
                "started_at": group_run.started_at,
                "ended_at": group_run.ended_at,
                "log_url": group_run.log_url,
            },
        ],
    }
