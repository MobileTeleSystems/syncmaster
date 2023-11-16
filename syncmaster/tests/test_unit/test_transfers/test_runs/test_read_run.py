import pytest
from httpx import AsyncClient
from tests.utils import MockGroup, MockRun, MockUser, TestUserRoles

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_read_run(
    client: AsyncClient,
    group_run: MockRun,
) -> None:
    result = await client.get(f"v1/transfers/{group_run.transfer.id}/runs/{group_run.id}")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_groupless_user_can_not_read_run_of_the_transfer(
    client: AsyncClient,
    group_run: MockRun,
    simple_user: MockUser,
) -> None:
    result = await client.get(
        f"v1/transfers/{group_run.transfer.id}/runs/{group_run.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }


async def test_group_owner_can_read_run_of_transfer_his_group(
    client: AsyncClient,
    group_run: MockRun,
    simple_user: MockUser,
):
    result = await client.get(
        f"v1/transfers/{group_run.transfer.id}/runs/{group_run.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }

    result = await client.get(
        f"v1/transfers/{group_run.transfer.id}/runs/{group_run.id}",
        headers={
            "Authorization": f"Bearer {group_run.transfer.owner_group.get_member_of_role(TestUserRoles.Owner).token}"
        },
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_run.id,
        "transfer_id": group_run.transfer_id,
        "status": group_run.status.value,
        "started_at": group_run.started_at,
        "ended_at": group_run.ended_at,
        "log_url": group_run.log_url,
        "transfer_dump": group_run.transfer_dump,
    }


async def test_group_owner_cannot_read_run_of_other_transfer(
    client: AsyncClient,
    empty_group: MockGroup,
    group_run: MockRun,
) -> None:
    result = await client.get(
        f"v1/transfers/{group_run.transfer.id}/runs/{group_run.id}",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(TestUserRoles.Owner).token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }


async def test_group_member_can_read_run_of_his_group_transfer(
    client: AsyncClient,
    group_run: MockRun,
) -> None:
    result = await client.get(
        f"v1/transfers/{group_run.transfer.id}/runs/{group_run.id}",
        headers={
            "Authorization": f"Bearer {group_run.transfer.owner_group.get_member_of_role(TestUserRoles.User).token}"
        },
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_run.id,
        "transfer_id": group_run.transfer_id,
        "status": group_run.status.value,
        "started_at": group_run.started_at,
        "ended_at": group_run.ended_at,
        "log_url": group_run.log_url,
        "transfer_dump": group_run.transfer_dump,
    }


async def test_superuser_can_read_any_runs_by_id(
    client: AsyncClient,
    superuser: MockUser,
    group_run: MockRun,
) -> None:
    result = await client.get(
        f"v1/transfers/{group_run.transfer.id}/runs/{group_run.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_run.id,
        "transfer_id": group_run.transfer_id,
        "status": group_run.status.value,
        "started_at": group_run.started_at,
        "ended_at": group_run.ended_at,
        "log_url": group_run.log_url,
        "transfer_dump": group_run.transfer_dump,
    }
