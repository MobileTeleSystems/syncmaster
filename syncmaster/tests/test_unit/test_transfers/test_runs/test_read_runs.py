import pytest
from httpx import AsyncClient
from tests.utils import MockGroup, MockRun, MockTransfer, MockUser, TestUserRoles

pytestmark = [pytest.mark.asyncio]


async def test_user_plus_can_read_runs_of_the_transfer(
    client: AsyncClient,
    group_run: MockRun,
    role_user_plus: TestUserRoles,
) -> None:
    # Arrange
    user = group_run.transfer.owner_group.get_member_of_role(role_user_plus)

    # Act
    result = await client.get(
        "v1/runs",
        headers={"Authorization": f"Bearer {user.token}"},
        params={"transfer_id": group_run.transfer.id},
    )

    # Assert
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
    assert result.status_code == 200


async def test_groupless_user_cannot_read_runs_transfer(
    client: AsyncClient,
    simple_user: MockUser,
    group_run: MockRun,
) -> None:
    # Act
    result = await client.get(
        "v1/runs",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        params={"transfer_id": group_run.transfer.id},
    )

    # Arrange
    assert result.json() == {
        "message": "Transfer not found",
        "ok": False,
        "status_code": 404,
    }
    assert result.status_code == 404


async def test_superuser_can_read_runs(
    client: AsyncClient,
    superuser: MockUser,
    group_run: MockRun,
) -> None:
    # Act
    result = await client.get(
        "v1/runs",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"transfer_id": group_run.transfer.id},
    )
    # Assert
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
    assert result.status_code == 200


async def test_unauthorized_user_cannot_read_run(
    client: AsyncClient,
    group_transfer: MockTransfer,
) -> None:
    # Act
    result = await client.get(
        "v1/runs",
        params={"transfer_id": group_transfer.id},
    )
    # Assert
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_other_group_member_cannot_read_runs_of_the_transfer(
    client: AsyncClient,
    group_run: MockRun,
    group: MockGroup,
    role_guest_plus: TestUserRoles,
) -> None:
    # Arrange
    user = group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.get(
        "v1/runs",
        headers={"Authorization": f"Bearer {user.token}"},
        params={"transfer_id": group_run.transfer.id},
    )

    # Assert
    assert result.json() == {
        "message": "Transfer not found",
        "ok": False,
        "status_code": 404,
    }


async def test_group_member_cannot_read_runs_of_the_unknown_transfer_error(
    client: AsyncClient,
    group_run: MockRun,
    role_guest_plus: TestUserRoles,
) -> None:
    # Arrange
    user = group_run.transfer.owner_group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.get(
        "v1/runs",
        headers={"Authorization": f"Bearer {user.token}"},
        params={"transfer_id": -1},
    )

    # Assert
    assert result.json() == {
        "message": "Transfer not found",
        "ok": False,
        "status_code": 404,
    }


async def test_superuser_cannot_read_runs_of_unknown_transfer_error(
    client: AsyncClient,
    superuser: MockUser,
    group_run: MockRun,
) -> None:
    # Act
    result = await client.get(
        "v1/runs",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"transfer_id": -1},
    )
    # Assert
    assert result.json() == {
        "message": "Transfer not found",
        "ok": False,
        "status_code": 404,
    }
