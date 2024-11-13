import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Queue, Transfer
from tests.mocks import MockConnection, MockGroup, MockTransfer, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_developer_plus_can_create_transfer(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    session: AsyncSession,
    role_developer_plus: UserTestRoles,
    group_queue: Queue,
    mock_group: MockGroup,
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
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
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


async def test_guest_cannot_create_transfer(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    mock_group: MockGroup,
    group_queue: Queue,
):
    # Arrange
    first_connection, second_connection = two_group_connections
    user = mock_group.get_member_of_role(UserTestRoles.Guest)

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": mock_group.id,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_connection.id,
            "target_connection_id": second_connection.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
            "queue_id": group_queue.id,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }


async def test_groupless_user_cannot_create_transfer(
    client: AsyncClient,
    simple_user: MockUser,
    two_group_connections: tuple[MockConnection, MockConnection],
    group_queue: Queue,
):
    # Arrange
    first_conn, second_conn = two_group_connections

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "group_id": first_conn.owner_group.group.id,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.id,
            "target_connection_id": second_conn.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
            "queue_id": group_queue.id,
        },
    )

    # Assert
    assert result.status_code == 403
    assert result.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }


async def test_other_group_user_plus_cannot_create_group_transfer(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    group: MockGroup,
    role_developer_plus: UserTestRoles,
    group_queue: Queue,
):
    # Arrange
    first_conn, second_conn = two_group_connections
    user = group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": first_conn.owner_group.id,
            "name": "new test group transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.id,
            "target_connection_id": second_conn.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
            "queue_id": group_queue.id,
        },
    )
    assert result.status_code == 403
    assert result.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }


async def test_superuser_can_create_transfer(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    session: AsyncSession,
    superuser: MockUser,
    mock_group: MockGroup,
    group_queue: Queue,
):
    # Arrange
    first_conn, second_conn = two_group_connections

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "group_id": mock_group.id,
            "name": "new test group transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.id,
            "target_connection_id": second_conn.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
            "queue_id": group_queue.id,
        },
    )
    transfer = (
        await session.scalars(
            select(Transfer).filter_by(
                name="new test group transfer",
                group_id=mock_group.id,
            ),
        )
    ).one()

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


@pytest.mark.parametrize(
    argnames=["new_data", "error_json"],
    argvalues=(
        (
            {"name": ""},
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "location": ["body", "name"],
                            "message": "String should have at least 1 character",
                            "code": "string_too_short",
                            "context": {"min_length": 1},
                            "input": "",
                        },
                    ],
                },
            },
        ),
        (
            {"name": None},
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "location": ["body", "name"],
                            "message": "Input should be a valid string",
                            "code": "string_type",
                            "context": {},
                            "input": None,
                        },
                    ],
                },
            },
        ),
        (
            {"is_scheduled": 2},
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "location": ["body", "is_scheduled"],
                            "message": "Input should be a valid boolean, unable to interpret input",
                            "code": "bool_parsing",
                            "context": {},
                            "input": 2,
                        },
                    ],
                },
            },
        ),
        (
            {"schedule": None},
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "location": ["body"],
                            "message": "Value error, If transfer must be scheduled than set schedule param",
                            "code": "value_error",
                            "context": {},
                            "input": {
                                "description": "",
                                "group_id": 1,
                                "is_scheduled": True,
                                "name": "new test transfer",
                                "queue_id": 1,
                                "schedule": None,
                                "source_connection_id": 1,
                                "source_params": {"table_name": "source_table", "type": "postgres"},
                                "strategy_params": {"type": "full"},
                                "target_connection_id": 2,
                                "target_params": {"table_name": "target_table", "type": "postgres"},
                            },
                        },
                    ],
                },
            },
        ),
        (
            {
                "strategy_params": {"type": "new some strategy type"},
            },
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "location": ["body", "strategy_params"],
                            "message": (
                                "Input tag 'new some strategy type' found using 'type' "
                                "does not match any of the expected tags: 'full', 'incremental'"
                            ),
                            "code": "union_tag_invalid",
                            "context": {
                                "discriminator": "'type'",
                                "expected_tags": "'full', 'incremental'",
                                "tag": "new some strategy type",
                            },
                            "input": {"type": "new some strategy type"},
                        },
                    ],
                },
            },
        ),
        (
            {
                "source_params": {
                    "type": "new some connection type",
                    "table_name": "source_table",
                },
            },
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "location": ["body", "source_params"],
                            "message": (
                                "Input tag 'new some connection type' found using 'type' "
                                "does not match any of the expected tags: 'postgres', 'hdfs', 'hive', 'oracle', 'clickhouse', 'mssql', 'mysql', 's3'"
                            ),
                            "code": "union_tag_invalid",
                            "context": {
                                "discriminator": "'type'",
                                "expected_tags": "'postgres', 'hdfs', 'hive', 'oracle', 'clickhouse', 'mssql', 'mysql', 's3'",
                                "tag": "new some connection type",
                            },
                            "input": {
                                "table_name": "source_table",
                                "type": "new some connection type",
                            },
                        },
                    ],
                },
            },
        ),
    ),
)
async def test_check_fields_validation_on_create_transfer(
    new_data: dict,
    error_json: dict,
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    role_developer_plus: UserTestRoles,
    mock_group: MockGroup,
    group_queue: Queue,
):
    # Arrange
    first_conn, second_conn = two_group_connections
    user = mock_group.get_member_of_role(role_developer_plus)

    # Act
    transfer_data = {
        "name": "new test transfer",
        "group_id": mock_group.id,
        "description": "",
        "is_scheduled": True,
        "schedule": "",
        "source_connection_id": first_conn.id,
        "target_connection_id": second_conn.id,
        "source_params": {"type": "postgres", "table_name": "source_table"},
        "target_params": {"type": "postgres", "table_name": "target_table"},
        "strategy_params": {"type": "full"},
        "queue_id": group_queue.id,
    }
    transfer_data.update(new_data)
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json=transfer_data,
    )

    # Assert
    assert result.status_code == 422

    if new_data == {"schedule": None}:
        error_json["error"]["details"][0]["input"] = transfer_data

    assert result.json() == error_json


async def test_check_connection_types_and_its_params_on_create_transfer(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    role_developer_plus: UserTestRoles,
    mock_group: MockGroup,
    group_queue: Queue,
):
    # Arrange
    first_conn, second_conn = two_group_connections
    user = mock_group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "new test transfer",
            "group_id": mock_group.id,
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.connection.id,
            "target_connection_id": second_conn.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "oracle", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
            "queue_id": group_queue.id,
        },
    )

    # Assert
    assert result.status_code == 400
    assert result.json() == {
        "error": {
            "code": "bad_request",
            "message": "Target connection has type `postgres` but its params has `oracle` type",
            "details": None,
        },
    }


async def test_check_different_connections_owner_group_on_create_transfer(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
    mock_group: MockGroup,
    group_queue: Queue,
):
    # Arrange
    first_conn, _ = two_group_connections
    user = mock_group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "new test transfer",
            "group_id": mock_group.id,
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.connection.id,
            "target_connection_id": group_connection.connection.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
            "queue_id": group_queue.id,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "bad_request",
            "message": "Connections should belong to the transfer group",
            "details": None,
        },
    }
    assert result.status_code == 400


async def test_unauthorized_user_cannot_create_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    # Act
    result = await client.post(
        "v1/transfers",
        json={
            "group_id": group_transfer.owner_group.group.id,
            "name": "New transfer name",
            "source_connection_id": group_transfer.source_connection_id,
            "target_connection_id": group_transfer.target_connection_id,
            "source_params": {"type": "postgres", "table_name": "test"},
            "target_params": {"type": "postgres", "table_name": "test1"},
            "queue_id": group_queue.id,
        },
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


async def test_developer_plus_cannot_create_transfer_with_other_group_queue(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    role_developer_plus: UserTestRoles,
    group_transfer: MockTransfer,
):
    # Arrange
    first_conn, second_conn = two_group_connections
    user = first_conn.owner_group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": first_conn.owner_group.group.id,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.id,
            "target_connection_id": second_conn.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
            "queue_id": group_transfer.transfer.queue_id,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "bad_request",
            "message": "Queue should belong to the transfer group",
            "details": None,
        },
    }


async def test_developer_plus_can_not_create_transfer_with_target_format_json(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    session: AsyncSession,
    role_developer_plus: UserTestRoles,
    group_queue: Queue,
    mock_group: MockGroup,
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
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {
                "type": "s3",
                "directory_path": "/some/dir",
                "df_schema": {},
                "options": {},
                "file_format": {
                    "type": "json",
                    "lineSep": "\n",
                    "encoding": "utf-8",
                },
            },
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
                    "context": {"discriminator": "'type'", "tag": "json", "expected_tags": "'csv', 'jsonline'"},
                    "input": {"type": "json", "lineSep": "\n", "encoding": "utf-8"},
                    "location": ["body", "target_params", "s3", "file_format"],
                    "message": "Input tag 'json' found using 'type' does not match any of the expected tags: 'csv', 'jsonline'",
                    "code": "union_tag_invalid",
                },
            ],
        },
    }


async def test_superuser_cannot_create_transfer_with_other_group_queue(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    group_transfer: MockTransfer,
    superuser: MockUser,
):
    # Arrange
    first_conn, second_conn = two_group_connections

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "group_id": first_conn.owner_group.group.id,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.id,
            "target_connection_id": second_conn.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
            "queue_id": group_transfer.transfer.queue_id,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "bad_request",
            "message": "Queue should belong to the transfer group",
            "details": None,
        },
    }


@pytest.mark.parametrize("iter_conn_id", [(False, True), (True, False)])
async def test_group_member_cannot_create_transfer_with_unknown_connection_error(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    role_developer_plus: UserTestRoles,
    iter_conn_id: tuple,
    mock_group: MockGroup,
    group_queue: Queue,
):
    # Arrange
    first_conn, second_conn = two_group_connections
    user = mock_group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": first_conn.owner_group.group.id,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.id if iter_conn_id[0] else -1,
            "target_connection_id": second_conn.id if iter_conn_id[1] else -1,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
            "queue_id": group_queue.id,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }


async def test_developer_plus_cannot_create_transfer_with_unknown_group_error(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    role_developer_plus: UserTestRoles,
    group_queue: Queue,
):
    # Arrange
    first_conn, second_conn = two_group_connections
    user = first_conn.owner_group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": -1,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.id,
            "target_connection_id": second_conn.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
            "queue_id": group_queue.id,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


@pytest.mark.parametrize("conn_id", [(False, True), (True, False)])
async def test_superuser_cannot_create_transfer_with_unknown_connection_error(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    conn_id: tuple,
    superuser: MockUser,
    group_queue: Queue,
):
    # Arrange
    first_conn, second_conn = two_group_connections

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "group_id": first_conn.owner_group.group.id,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.id if conn_id[0] else -1,
            "target_connection_id": second_conn.id if conn_id[1] else -1,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
            "queue_id": group_queue.id,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }


async def test_developer_plus_cannot_create_transfer_with_unknown_queue_error(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    role_developer_plus: UserTestRoles,
):
    # Arrange
    first_conn, second_conn = two_group_connections
    user = first_conn.owner_group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": first_conn.owner_group.group.id,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.id,
            "target_connection_id": second_conn.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
            "queue_id": -1,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Queue not found",
            "details": None,
        },
    }


async def test_superuser_cannot_create_transfer_with_unknown_group_error(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    superuser: MockUser,
    group_queue: Queue,
):
    # Arrange
    first_conn, second_conn = two_group_connections

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "group_id": -1,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.id,
            "target_connection_id": second_conn.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
            "queue_id": group_queue.id,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_superuser_cannot_create_transfer_with_unknown_queue_error(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    superuser: MockUser,
):
    # Arrange
    first_conn, second_conn = two_group_connections

    # Act
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "group_id": first_conn.owner_group.group.id,
            "name": "new test transfer",
            "description": "",
            "is_scheduled": False,
            "schedule": "",
            "source_connection_id": first_conn.id,
            "target_connection_id": second_conn.id,
            "source_params": {"type": "postgres", "table_name": "source_table"},
            "target_params": {"type": "postgres", "table_name": "target_table"},
            "strategy_params": {"type": "full"},
            "queue_id": -1,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Queue not found",
            "details": None,
        },
    }
