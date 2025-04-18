import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import RunType, Status
from tests.mocks import MockGroup, MockRun, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_developer_plus_can_stop_run_of_transfer_his_group(
    client: AsyncClient,
    group_run: MockRun,
    session: AsyncSession,
    role_developer_plus: UserTestRoles,
) -> None:
    user = group_run.transfer.owner_group.get_member_of_role(role_developer_plus)

    result = await client.post(
        f"v1/runs/{group_run.id}/stop",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    await session.refresh(group_run.run)
    assert group_run.status == Status.SEND_STOP_SIGNAL

    assert result.status_code == 200, result.json()
    assert result.json() == {
        "id": group_run.id,
        "transfer_id": group_run.transfer_id,
        "status": group_run.status.value,
        "log_url": group_run.log_url,
        "started_at": group_run.started_at,
        "ended_at": group_run.ended_at,
        "transfer_dump": group_run.transfer_dump,
        "type": RunType.MANUAL,
    }


async def test_groupless_user_cannot_stop_run(
    client: AsyncClient,
    simple_user: MockUser,
    group_run: MockRun,
    session: AsyncSession,
) -> None:
    result = await client.post(
        f"v1/runs/{group_run.id}/stop",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }


async def test_other_group_member_cannot_stop_run_of_other_group_transfer(
    client: AsyncClient,
    group_run: MockRun,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
    session: AsyncSession,
) -> None:
    # Arrenge
    user = group.get_member_of_role(role_guest_plus)

    result = await client.post(
        f"v1/runs/{group_run.id}/stop",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }
    await session.refresh(group_run.run)
    assert group_run.status != Status.SEND_STOP_SIGNAL


async def test_superuser_can_stop_run(
    client: AsyncClient,
    superuser: MockUser,
    group_run: MockRun,
    session: AsyncSession,
) -> None:
    result = await client.post(
        f"v1/runs/{group_run.id}/stop",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    await session.refresh(group_run.run)
    assert group_run.status == Status.SEND_STOP_SIGNAL

    assert result.status_code == 200, result.json()
    assert result.json() == {
        "id": group_run.id,
        "transfer_id": group_run.transfer_id,
        "status": group_run.status.value,
        "log_url": group_run.log_url,
        "started_at": group_run.started_at,
        "ended_at": group_run.ended_at,
        "transfer_dump": group_run.transfer_dump,
        "type": RunType.MANUAL,
    }


@pytest.mark.parametrize("status", (Status.SEND_STOP_SIGNAL, Status.FINISHED, Status.FAILED, Status.STOPPED))
async def test_developer_plus_cannot_stop_run_in_status_except_started_or_created(
    status: Status,
    client: AsyncClient,
    group_run: MockRun,
    session: AsyncSession,
    role_developer_plus: UserTestRoles,
) -> None:
    user = group_run.transfer.owner_group.get_member_of_role(role_developer_plus)
    group_run.run.status = status
    session.add(group_run.run)
    await session.commit()

    result = await client.post(
        f"v1/runs/{group_run.id}/stop",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert result.status_code == 400, result.json()
    assert result.json() == {
        "error": {
            "code": "bad_request",
            "message": f"Cannot stop run {group_run.id}. Current status is {group_run.status}",
            "details": None,
        },
    }


async def test_unauthorized_user_cannot_stop_run(
    client: AsyncClient,
    group_run: MockRun,
) -> None:
    result = await client.post(f"v1/runs/{group_run.id}/stop")

    assert result.status_code == 401, result.json()
    assert result.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_developer_plus_cannot_stop_unknown_run_of_transfer_error(
    client: AsyncClient,
    group_run: MockRun,
    session: AsyncSession,
    role_developer_plus: UserTestRoles,
) -> None:
    user = group_run.transfer.owner_group.get_member_of_role(role_developer_plus)

    result = await client.post(
        "v1/runs/-1/stop",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    await session.refresh(group_run.run)
    assert group_run.status == Status.CREATED

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Run not found",
            "details": None,
        },
    }


async def test_superuser_cannot_stop_unknown_run_error(
    client: AsyncClient,
    superuser: MockUser,
    group_run: MockRun,
    session: AsyncSession,
) -> None:
    result = await client.post(
        "v1/runs/-1/stop",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    await session.refresh(group_run.run)
    assert group_run.status == Status.CREATED

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Run not found",
            "details": None,
        },
    }
