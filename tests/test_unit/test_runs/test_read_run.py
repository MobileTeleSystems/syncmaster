import pytest
from httpx import AsyncClient

from syncmaster.db.models import RunType
from tests.mocks import MockGroup, MockRun, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_developer_plus_can_read_run(
    client: AsyncClient,
    group_run: MockRun,
    role_developer_plus: UserTestRoles,
):
    # Arrange
    user = group_run.transfer.owner_group.get_member_of_role(role_developer_plus)

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
        "type": RunType.MANUAL,
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
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }
    assert result.status_code == 404


async def test_another_group_member_cannot_read_run(
    client: AsyncClient,
    group_run: MockRun,
    role_guest_plus: UserTestRoles,
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
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
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
        "type": RunType.MANUAL,
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
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }
    assert result.status_code == 401


async def test_group_member_cannot_read_unknown_run_error(
    client: AsyncClient,
    group_run: MockRun,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    user = group_run.transfer.owner_group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.get(
        "v1/runs/-1",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Run not found",
            "details": None,
        },
    }


async def test_superuser_cannot_read_unknown_run_error(
    client: AsyncClient,
    superuser: MockUser,
    group_run: MockRun,
) -> None:
    # Act
    result = await client.get(
        "v1/runs/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Run not found",
            "details": None,
        },
    }
