import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Queue, Transfer
from tests.mocks import MockConnection, MockGroup, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


@pytest.mark.parametrize(
    "create_connection_data",
    [
        {
            "type": "s3",
            "host": "localhost",
            "port": 443,
        },
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    "target_source_params",
    [
        {
            "type": "s3",
            "directory_path": "/some/pure/path",
            "file_format": {
                "type": "csv",
            },
            "options": {
                "some": "option",
            },
        },
    ],
)
async def test_developer_plus_can_create_s3_transfer(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    session: AsyncSession,
    role_developer_plus: UserTestRoles,
    group_queue: Queue,
    mock_group: MockGroup,
    target_source_params: dict,
    create_connection_data: dict,
):
    # Arrange
    first_connection, second_connection = two_group_connections
    user = mock_group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": mock_group.group.id,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_connection.id,
            "target_connection_id": second_connection.id,
            "source_params": target_source_params,
            "target_params": target_source_params,
            "strategy_params": {"type": "full"},
            "queue_id": group_queue.id,
        },
    )

    # Pre-Assert
    transfer = (
        await session.scalars(
            select(Transfer).filter_by(
                name="new test transfer",
                group_id=mock_group.group.id,
            ),
        )
    ).one()
    # Assert
    assert result.status_code == 200
    assert result.json() == {
        "id": transfer.id,
        "group_id": transfer.group_id,
        "name": transfer.name,
        "description": transfer.description,
        "schedule": transfer.schedule,
        "is_scheduled": transfer.is_scheduled,
        "source_connection_id": transfer.source_connection_id,
        "target_connection_id": transfer.target_connection_id,
        "source_params": transfer.source_params,
        "target_params": transfer.target_params,
        "strategy_params": transfer.strategy_params,
        "queue_id": transfer.queue_id,
    }

    for params in (transfer.source_params, transfer.target_params):
        assert params["type"] == "s3"
        assert params["directory_path"] == "/some/pure/path"
        assert params["file_format"]["type"] == "csv"
        assert params["options"] == {"some": "option"}


@pytest.mark.parametrize(
    "create_connection_data",
    [
        {
            "type": "hdfs",
            "cluster": "cluster",
        },
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    "target_source_params",
    [
        {
            "type": "hdfs",
            "directory_path": "/some/pure/path",
            "file_format": {
                "type": "csv",
            },
        },
    ],
)
async def test_developer_plus_can_create_hdfs_transfer(
    create_connection_data: dict,
    two_group_connections: tuple[MockConnection, MockConnection],
    target_source_params: dict,
    role_developer_plus: UserTestRoles,
    group_queue: Queue,
    mock_group: MockGroup,
    session: AsyncSession,
    client: AsyncClient,
):
    # Arrange
    first_connection, second_connection = two_group_connections
    user = mock_group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": mock_group.group.id,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_connection.id,
            "target_connection_id": second_connection.id,
            "source_params": target_source_params,
            "target_params": target_source_params,
            "strategy_params": {"type": "full"},
            "queue_id": group_queue.id,
        },
    )

    # Pre-Assert
    transfer = (
        await session.scalars(
            select(Transfer).filter_by(
                name="new test transfer",
                group_id=mock_group.group.id,
            ),
        )
    ).one()

    # Assert
    assert result.status_code == 200
    assert result.json() == {
        "id": transfer.id,
        "group_id": transfer.group_id,
        "name": transfer.name,
        "description": transfer.description,
        "schedule": transfer.schedule,
        "is_scheduled": transfer.is_scheduled,
        "source_connection_id": transfer.source_connection_id,
        "target_connection_id": transfer.target_connection_id,
        "source_params": transfer.source_params,
        "target_params": transfer.target_params,
        "strategy_params": transfer.strategy_params,
        "queue_id": transfer.queue_id,
    }

    for params in (transfer.source_params, transfer.target_params):
        assert params["type"] == "hdfs"
        assert params["directory_path"] == "/some/pure/path"
        assert params["file_format"]["type"] == "csv"
        assert params["options"] == {}


@pytest.mark.parametrize(
    "create_connection_data",
    [
        {
            "type": "s3",
            "host": "localhost",
            "port": 443,
        },
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    "target_source_params",
    [
        {
            "type": "s3",
            "directory_path": "some/path",
            "file_format": {
                "type": "csv",
            },
        },
    ],
)
async def test_cannot_create_file_transfer_with_relative_path(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    group_queue: Queue,
    mock_group: MockGroup,
    target_source_params: dict,
    create_connection_data: dict,
):
    # Arrange
    first_connection, second_connection = two_group_connections
    user = mock_group.get_member_of_role(UserTestRoles.Developer)

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": mock_group.group.id,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_connection.id,
            "target_connection_id": second_connection.id,
            "source_params": target_source_params,
            "target_params": target_source_params,
            "strategy_params": {"type": "full"},
            "queue_id": group_queue.id,
        },
    )

    # Assert
    assert result.status_code == 422
    assert result.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [
                {
                    "context": {},
                    "input": "some/path",
                    "location": ["body", "source_params", "s3", "directory_path"],
                    "message": "Value error, Directory path must be absolute",
                    "code": "value_error",
                },
                {
                    "context": {},
                    "input": "some/path",
                    "location": ["body", "target_params", "s3", "directory_path"],
                    "message": "Value error, Directory path must be absolute",
                    "code": "value_error",
                },
            ],
        },
    }
