import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Queue, Transfer
from tests.mocks import MockConnection, MockGroup, MockTransfer, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


@pytest.mark.parametrize("connection_type", ["ftp"], indirect=True)
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
            "source_params": {
                "type": "ftp",
                "directory_path": "/source_path",
                "file_format": {
                    "type": "csv",
                },
            },
            "target_params": {
                "type": "ftp",
                "directory_path": "/target_path",
                "file_format": {
                    "type": "csv",
                },
            },
            "strategy_params": {"type": "incremental", "increment_by": "file_modified_since"},
            "transformations": [
                {
                    "type": "dataframe_rows_filter",
                    "filters": [
                        {
                            "type": "equal",
                            "field": "col1",
                            "value": "something",
                        },
                        {
                            "type": "greater_than",
                            "field": "col2",
                            "value": "20",
                        },
                    ],
                },
                {
                    "type": "dataframe_columns_filter",
                    "filters": [
                        {
                            "type": "include",
                            "field": "col1",
                        },
                        {
                            "type": "rename",
                            "field": "col2",
                            "to": "new_col2",
                        },
                        {
                            "type": "cast",
                            "field": "col3",
                            "as_type": "VARCHAR",
                        },
                    ],
                },
                {
                    "type": "file_metadata_filter",
                    "filters": [
                        {
                            "type": "name_glob",
                            "value": "*.csv",
                        },
                        {
                            "type": "name_regexp",
                            "value": "^1234$",
                        },
                        {
                            "type": "file_size_min",
                            "value": "1kb",
                        },
                    ],
                },
            ],
            "resources": {
                "max_parallel_tasks": 1,
                "cpu_cores_per_task": 2,
                "ram_bytes_per_task": 1024**3,
            },
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
    assert result.status_code == 200, result.json()
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
        "transformations": transfer.transformations,
        "resources": transfer.resources,
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
    assert result.status_code == 403, result.json()
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
    assert result.status_code == 403, result.json()
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
            "transformations": [
                {
                    "type": "dataframe_rows_filter",
                    "filters": [
                        {
                            "type": "equal",
                            "field": "col1",
                            "value": "something",
                        },
                        {
                            "type": "greater_than",
                            "field": "col2",
                            "value": "20",
                        },
                    ],
                },
            ],
            "resources": {
                "max_parallel_tasks": 3,
                "cpu_cores_per_task": 2,
                "ram_bytes_per_task": 1024**3,
            },
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

    assert result.status_code == 200, result.json()
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
        "transformations": transfer.transformations,
        "resources": transfer.resources,
        "queue_id": transfer.queue_id,
    }


# TODO: refactor annotations & fixtures
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
                    "type": "ftp",
                    "directory_path": "/source_path",
                    "file_format": {
                        "type": "csv",
                    },
                },
                "strategy_params": {
                    "type": "incremental",
                    "increment_by": "unknown",
                },
            },
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "location": ["body"],
                            "message": (
                                "Value error, Field 'increment_by' must be equal to 'file_modified_since' or 'file_name' for file source types"
                            ),
                            "code": "value_error",
                            "context": {},
                        },
                    ],
                },
            },
        ),
        (
            {
                "source_params": {
                    "type": "s3",
                    "directory_path": "/source_path",
                    "file_format": {
                        "type": "csv",
                    },
                },
                "strategy_params": {
                    "type": "incremental",
                    "increment_by": "file_modified_since",
                },
            },
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "location": ["body"],
                            "message": ("Value error, S3 and HDFS sources do not support incremental strategy for now"),
                            "code": "value_error",
                            "context": {},
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
                                "does not match any of the expected tags: 'postgres', 'hive', 'oracle', 'clickhouse', 'mssql', 'mysql', 'hdfs', 's3', 'sftp', 'ftp', 'ftps', 'webdav', 'samba'"
                            ),
                            "code": "union_tag_invalid",
                            "context": {
                                "discriminator": "'type'",
                                "expected_tags": "'postgres', 'hive', 'oracle', 'clickhouse', 'mssql', 'mysql', 'hdfs', 's3', 'sftp', 'ftp', 'ftps', 'webdav', 'samba'",
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
        (
            {
                "transformations": [
                    {
                        "type": "some unknown transformation type",
                        "filters": [
                            {
                                "type": "equal",
                                "field": "col1",
                                "value": "something",
                            },
                        ],
                    },
                ],
            },
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "location": ["body", "transformations", 0],
                            "message": (
                                "Input tag 'some unknown transformation type' found using 'type' "
                                "does not match any of the expected tags: 'dataframe_rows_filter', 'dataframe_columns_filter', 'file_metadata_filter'"
                            ),
                            "code": "union_tag_invalid",
                            "context": {
                                "discriminator": "'type'",
                                "expected_tags": "'dataframe_rows_filter', 'dataframe_columns_filter', 'file_metadata_filter'",
                                "tag": "some unknown transformation type",
                            },
                            "input": {
                                "type": "some unknown transformation type",
                                "filters": [
                                    {
                                        "type": "equal",
                                        "field": "col1",
                                        "value": "something",
                                    },
                                ],
                            },
                        },
                    ],
                },
            },
        ),
        (
            {
                "transformations": [
                    {
                        "type": "dataframe_rows_filter",
                        "filters": [
                            {
                                "type": "equals_today",
                                "field": "col1",
                                "value": "something",
                            },
                        ],
                    },
                ],
            },
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "location": ["body", "transformations", 0, "dataframe_rows_filter", "filters", 0],
                            "message": (
                                "Input tag 'equals_today' found using 'type' does not match any of the expected tags: 'is_null', 'is_not_null', 'equal', 'not_equal', "
                                "'greater_than', 'greater_or_equal', 'less_than', 'less_or_equal', 'like', 'ilike', 'not_like', 'not_ilike', 'regexp'"
                            ),
                            "code": "union_tag_invalid",
                            "context": {
                                "discriminator": "'type'",
                                "tag": "equals_today",
                                "expected_tags": "'is_null', 'is_not_null', 'equal', 'not_equal', 'greater_than', 'greater_or_equal', 'less_than', 'less_or_equal', 'like', 'ilike', 'not_like', 'not_ilike', 'regexp'",
                            },
                            "input": {
                                "type": "equals_today",
                                "field": "col1",
                                "value": "something",
                            },
                        },
                    ],
                },
            },
        ),
        (
            {
                "transformations": [
                    {
                        "type": "dataframe_columns_filter",
                        "filters": [
                            {
                                "type": "convert",
                                "field": "col1",
                                "value": "VARCHAR",
                            },
                        ],
                    },
                ],
            },
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "location": ["body", "transformations", 0, "dataframe_columns_filter", "filters", 0],
                            "message": (
                                "Input tag 'convert' found using 'type' does not match any of the expected tags: 'include', 'rename', 'cast'"
                            ),
                            "code": "union_tag_invalid",
                            "context": {
                                "discriminator": "'type'",
                                "tag": "convert",
                                "expected_tags": "'include', 'rename', 'cast'",
                            },
                            "input": {
                                "type": "convert",
                                "field": "col1",
                                "value": "VARCHAR",
                            },
                        },
                    ],
                },
            },
        ),
        (
            {
                "transformations": [
                    {
                        "type": "file_metadata_filter",
                        "filters": [
                            {
                                "type": "glob",
                                "value": "*.csv",
                            },
                        ],
                    },
                ],
            },
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "location": ["body", "transformations", 0, "file_metadata_filter", "filters", 0],
                            "message": (
                                "Input tag 'glob' found using 'type' does not match any of the expected tags: 'name_glob', 'name_regexp', 'file_size_min', 'file_size_max'"
                            ),
                            "code": "union_tag_invalid",
                            "context": {
                                "discriminator": "'type'",
                                "tag": "glob",
                                "expected_tags": "'name_glob', 'name_regexp', 'file_size_min', 'file_size_max'",
                            },
                            "input": {
                                "type": "glob",
                                "value": "*.csv",
                            },
                        },
                    ],
                },
            },
        ),
        (
            {
                "transformations": [
                    {
                        "type": "file_metadata_filter",
                        "filters": [
                            {
                                "type": "name_glob",
                                "value": ".csv",
                            },
                        ],
                    },
                ],
            },
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "location": [
                                "body",
                                "transformations",
                                0,
                                "file_metadata_filter",
                                "filters",
                                0,
                                "name_glob",
                                "value",
                            ],
                            "message": "Value error, Invalid glob: '.csv'",
                            "code": "value_error",
                            "context": {},
                            "input": ".csv",
                        },
                    ],
                },
            },
        ),
        (
            {
                "transformations": [
                    {
                        "type": "file_metadata_filter",
                        "filters": [
                            {
                                "type": "name_regexp",
                                "value": "[a-z",
                            },
                        ],
                    },
                ],
            },
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "location": [
                                "body",
                                "transformations",
                                0,
                                "file_metadata_filter",
                                "filters",
                                0,
                                "name_regexp",
                                "value",
                            ],
                            "message": "Value error, Invalid regexp: '[a-z'",
                            "code": "value_error",
                            "context": {},
                            "input": "[a-z",
                        },
                    ],
                },
            },
        ),
        (
            {
                "resources": {
                    "max_parallel_tasks": 1,
                    "cpu_cores_per_task": 2,
                    "ram_bytes_per_task": 1024,
                },
            },
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "location": [
                                "body",
                                "resources",
                                "ram_bytes_per_task",
                            ],
                            "message": f"Input should be greater than or equal to {512 * 1024**2}",
                            "code": "greater_than_equal",
                            "context": {
                                "ge": 512 * 1024**2,
                            },
                            "input": 1024,
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
        "transformations": [],
        "queue_id": group_queue.id,
    }
    transfer_data.update(new_data)
    result = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json=transfer_data,
    )

    # Assert
    assert result.status_code == 422, result.json()
    if (
        (new_data == {"schedule": None})
        or ("strategy_params" in new_data and new_data["strategy_params"].get("increment_by") == "unknown")
        or (
            "strategy_params" in new_data
            and new_data["strategy_params"].get("type") == "incremental"
            and "source_params" in new_data
            and new_data["source_params"].get("type") == "s3"
        )
    ):
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
    assert result.status_code == 400, result.json()
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
    assert result.status_code == 400, result.json()


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
    assert result.status_code == 401, result.json()
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


async def test_developer_plus_cannot_create_transfer_with_target_format_json(
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
    assert result.status_code == 422, result.json()
    assert result.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [
                {
                    "context": {
                        "discriminator": "'type'",
                        "tag": "json",
                        "expected_tags": "'csv', 'jsonline', 'excel', 'xml', 'orc', 'parquet'",
                    },
                    "input": {"type": "json", "lineSep": "\n", "encoding": "utf-8"},
                    "location": ["body", "target_params", "s3", "file_format"],
                    "message": "Input tag 'json' found using 'type' does not match any of the expected tags: 'csv', 'jsonline', 'excel', 'xml', 'orc', 'parquet'",
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
