from datetime import datetime
from typing import Any

import pytest
from httpx import AsyncClient

from syncmaster.db.models import RunType, Status
from tests.mocks import MockGroup, MockRun, MockTransfer, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]

FUTURE_DATE = "2099-01-01T00:00:00"
PAST_DATE = "2000-01-01T00:00:00"


def format_datetime(dt: datetime) -> str:
    return dt.isoformat()


async def test_developer_plus_can_read_runs_of_the_transfer(
    client: AsyncClient,
    group_run: MockRun,
    role_developer_plus: UserTestRoles,
) -> None:
    # Arrange
    user = group_run.transfer.owner_group.get_member_of_role(role_developer_plus)

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
                "type": RunType.MANUAL,
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
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
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
                "type": RunType.MANUAL,
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
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_other_group_member_cannot_read_runs_of_the_transfer(
    client: AsyncClient,
    group_run: MockRun,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
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
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }


async def test_group_member_cannot_read_runs_of_the_unknown_transfer_error(
    client: AsyncClient,
    group_run: MockRun,
    role_guest_plus: UserTestRoles,
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
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
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
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }


@pytest.mark.parametrize(
    "filter_params, expected_total",
    [
        ({}, 6),  # No filters applied, expecting all runs (one run without started_at, ended_at)
        ({"status": [Status.CREATED.value]}, 1),
        ({"status": [Status.STARTED.value, Status.FAILED.value]}, 2),
        ({"started_at_since": PAST_DATE}, 5),
        ({"started_at_until": FUTURE_DATE}, 5),
        (
            {
                "started_at_since": PAST_DATE,
                "started_at_until": FUTURE_DATE,
            },
            5,
        ),
        (
            {
                "status": [Status.STARTED.value, Status.FAILED.value],
                "started_at_since": PAST_DATE,
                "started_at_until": FUTURE_DATE,
            },
            2,
        ),
    ],
    ids=[
        "no_filters",
        "status_single",
        "status_multiple",
        "started_at_since",
        "started_at_until",
        "started_at_range",
        "status_and_started_at_range",
    ],
)
async def test_filter_runs(
    client: AsyncClient,
    superuser: MockUser,
    group_runs: list[MockRun],
    filter_params: dict[str, Any],
    expected_total: int,
):
    # Arrange
    transfer_id = group_runs[0].run.transfer_id
    params = {"transfer_id": transfer_id}

    params.update(filter_params)

    # Act
    result = await client.get(
        "v1/runs",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params=params,
    )

    # Assert
    assert result.status_code == 200
    assert result.json()["meta"]["total"] == expected_total
    assert len(result.json()["items"]) == expected_total

    # check that the statuses match
    if "status" in params and params["status"]:
        status_filter = params["status"]
        returned_statuses = [run["status"] for run in result.json()["items"]]
        assert all(status in status_filter for status in returned_statuses)


@pytest.mark.parametrize(
    "params",
    [
        {
            "status": [Status.SEND_STOP_SIGNAL.value],
            "started_at_since": FUTURE_DATE,
        },
        {
            "status": [Status.STOPPED.value],
            "started_at_until": PAST_DATE,
        },
        {
            "started_at_since": FUTURE_DATE,
        },
        {
            "started_at_until": PAST_DATE,
        },
    ],
    ids=[
        "future_started_at_since",
        "past_started_at_until",
        "future_started_at_since_no_status",
        "past_started_at_until_no_status",
    ],
)
async def test_filter_runs_no_results(
    client: AsyncClient,
    superuser: MockUser,
    group_runs: list[MockRun],
    params: dict[str, Any],
):
    # Arrange
    transfer_id = group_runs[0].run.transfer_id
    computed_params = {"transfer_id": transfer_id}

    computed_params.update(params)

    # Act
    result = await client.get(
        "v1/runs",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params=computed_params,
    )

    # Assert
    assert result.status_code == 200
    data = result.json()
    assert data["items"] == []
    assert data["meta"]["total"] == 0
