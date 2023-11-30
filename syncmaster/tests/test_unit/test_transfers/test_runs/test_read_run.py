import pytest
from httpx import AsyncClient
from tests.utils import MockGroup, MockRun, MockUser, TestUserRoles

pytestmark = [pytest.mark.asyncio]


async def test_user_plus_can_read_run(
    client: AsyncClient,
    group_run: MockRun,
    role_user_plus: TestUserRoles,
):
    # Arrange
    user = group_run.transfer.owner_group.get_member_of_role(role_user_plus)

    # Act
    result = await client.get(
        f"v1/runs/{group_run.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.json() == {
        "id": group_run.id,
        "transfer_id": group_run.transfer_id,
        "status": group_run.status.value,
        "started_at": group_run.started_at,
        "ended_at": group_run.ended_at,
        "log_url": group_run.log_url,
        "transfer_dump": group_run.transfer_dump,
    }
    assert result.status_code == 200


async def test_groupless_user_cannot_read_run(
    client: AsyncClient,
    group_run: MockRun,
    simple_user: MockUser,
) -> None:
    # Act
    result = await client.get(
        f"v1/runs/{group_run.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }
    assert result.status_code == 404


async def test_another_group_member_cannot_read_run(
    client: AsyncClient,
    group_run: MockRun,
    role_guest_plus: TestUserRoles,
    group: MockGroup,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.get(
        f"v1/runs/{group_run.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.json() == {
        "message": "Transfer not found",
        "ok": False,
        "status_code": 404,
    }


async def test_superuser_can_read_runs(
    client: AsyncClient,
    superuser: MockUser,
    group_run: MockRun,
) -> None:
    # Act
    result = await client.get(
        f"v1/runs/{group_run.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    # Assert
    assert result.json() == {
        "id": group_run.id,
        "transfer_id": group_run.transfer_id,
        "status": group_run.status.value,
        "started_at": group_run.started_at,
        "ended_at": group_run.ended_at,
        "log_url": group_run.log_url,
        "transfer_dump": group_run.transfer_dump,
    }
    assert result.status_code == 200


async def test_unauthorized_user_cannot_read_run(
    client: AsyncClient,
    group_run: MockRun,
) -> None:
    # Act
    result = await client.get(f"v1/runs/{group_run.id}")

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }
    assert result.status_code == 401


async def test_group_member_cannot_read_unknown_run_error(
    client: AsyncClient,
    group_run: MockRun,
    role_guest_plus: TestUserRoles,
):
    # Arrange
    user = group_run.transfer.owner_group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.get(
        f"v1/runs/-1",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.json() == {
        "message": "Run not found",
        "ok": False,
        "status_code": 404,
    }


async def test_superuser_cannot_read_unknown_run_error(
    client: AsyncClient,
    superuser: MockUser,
    group_run: MockRun,
) -> None:
    # Act
    result = await client.get(
        f"v1/runs/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    # Assert
    assert result.json() == {
        "message": "Run not found",
        "ok": False,
        "status_code": 404,
    }
