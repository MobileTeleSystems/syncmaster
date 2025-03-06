import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Queue, Transfer
from tests.mocks import MockConnection, MockGroup, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


# TODO: refactor test fixtures to decrease amount of annotations
@pytest.mark.parametrize(
    "connection_type, create_connection_data",
    [
        (
            "s3",
            {
                "host": "localhost",
                "port": 443,
            },
        ),
    ],
    indirect=["create_connection_data"],
)
@pytest.mark.parametrize(
    "target_source_params, target_params",
    [
        (
            {
                "type": "s3",
                "directory_path": "/some/pure/path",
                "file_format": {
                    "type": "csv",
                    "delimiter": ",",
                    "encoding": "utf-8",
                    "quote": '"',
                    "escape": "\\",
                    "include_header": False,
                    "line_sep": "\n",
                    "compression": "gzip",
                },
                "options": {
                    "some": "option",
                },
            },
            {
                "file_name_template": "{run_created_at}_{index}.{extension}",
            },
        ),
        (
            {
                "type": "s3",
                "directory_path": "/some/excel/path",
                "file_format": {
                    "type": "excel",
                    "include_header": True,
                    "start_cell": "A1",
                },
                "options": {
                    "some": "option",
                },
            },
            {
                "file_name_template": "{run_id}-{index}.{extension}",
            },
        ),
        (
            {
                "type": "s3",
                "directory_path": "/some/xml/path",
                "file_format": {
                    "type": "xml",
                    "root_tag": "data",
                    "row_tag": "record",
                    "compression": "lz4",
                },
                "options": {
                    "some": "option",
                },
            },
            {
                "file_name_template": "{run_created_at}-{index}.{extension}",
            },
        ),
        (
            {
                "type": "s3",
                "directory_path": "/some/orc/path",
                "file_format": {
                    "type": "orc",
                },
                "options": {
                    "some": "option",
                },
            },
            {},
        ),
        (
            {
                "type": "s3",
                "directory_path": "/some/parquet/path",
                "file_format": {
                    "type": "parquet",
                    "compression": "gzip",
                },
                "options": {
                    "some": "option",
                },
            },
            {},
        ),
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
    target_params: dict,
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
            "target_params": {**target_source_params, **target_params},
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
        "transformations": transfer.transformations,
        "resources": transfer.resources,
        "queue_id": transfer.queue_id,
    }

    expected_file_formats = {
        "csv": {
            "type": "csv",
            "delimiter": ",",
            "encoding": "utf-8",
            "quote": '"',
            "escape": "\\",
            "include_header": False,
            "line_sep": "\n",
            "compression": "gzip",
        },
        "excel": {
            "type": "excel",
            "include_header": True,
            "start_cell": "A1",
        },
        "xml": {
            "type": "xml",
            "root_tag": "data",
            "row_tag": "record",
            "compression": "lz4",
        },
        "orc": {
            "type": "orc",
            "compression": "zlib",
        },
        "parquet": {
            "type": "parquet",
            "compression": "gzip",
        },
    }

    for params in (transfer.source_params, transfer.target_params):
        assert params["type"] == target_source_params["type"]
        assert params["directory_path"] == target_source_params["directory_path"]
        assert params["options"] == {"some": "option"}
        assert params["file_format"] == expected_file_formats[params["file_format"]["type"]]


@pytest.mark.parametrize(
    "connection_type,create_connection_data",
    [
        (
            "hdfs",
            {
                "cluster": "cluster",
            },
        ),
    ],
    indirect=["create_connection_data"],
)
@pytest.mark.parametrize(
    "target_source_params, target_params",
    [
        (
            {
                "type": "hdfs",
                "directory_path": "/some/pure/path",
                "file_format": {
                    "type": "csv",
                    "compression": "gzip",
                },
            },
            {
                "file_name_template": "{run_created_at}_{index}.{extension}",
            },
        ),
        (
            {
                "type": "hdfs",
                "directory_path": "/some/excel/path",
                "file_format": {
                    "type": "excel",
                    "include_header": True,
                    "start_cell": "A1",
                },
            },
            {
                "file_name_template": "{run_id}-{index}.{extension}",
            },
        ),
        (
            {
                "type": "hdfs",
                "directory_path": "/some/xml/path",
                "file_format": {
                    "type": "xml",
                    "root_tag": "data",
                    "row_tag": "record",
                    "compression": "bzip2",
                },
            },
            {
                "file_name_template": "{run_created_at}-{index}.{extension}",
            },
        ),
        (
            {
                "type": "hdfs",
                "directory_path": "/some/orc/path",
                "file_format": {
                    "type": "orc",
                },
            },
            {},
        ),
        (
            {
                "type": "hdfs",
                "directory_path": "/some/parquet/path",
                "file_format": {
                    "type": "parquet",
                    "compression": "snappy",
                },
            },
            {},
        ),
    ],
)
async def test_developer_plus_can_create_hdfs_transfer(
    create_connection_data: dict,
    two_group_connections: tuple[MockConnection, MockConnection],
    target_source_params: dict,
    target_params: dict,
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
            "target_params": {**target_source_params, **target_params},
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
        "transformations": transfer.transformations,
        "resources": transfer.resources,
        "queue_id": transfer.queue_id,
    }

    expected_file_formats = {
        "csv": {
            "type": "csv",
            "delimiter": ",",
            "encoding": "utf-8",
            "quote": '"',
            "escape": "\\",
            "include_header": False,
            "line_sep": "\n",
            "compression": "gzip",
        },
        "excel": {
            "type": "excel",
            "include_header": True,
            "start_cell": "A1",
        },
        "xml": {
            "type": "xml",
            "root_tag": "data",
            "row_tag": "record",
            "compression": "bzip2",
        },
        "orc": {
            "type": "orc",
            "compression": "zlib",
        },
        "parquet": {
            "type": "parquet",
            "compression": "snappy",
        },
    }

    for params in (transfer.source_params, transfer.target_params):
        assert params["type"] == target_source_params["type"]
        assert params["directory_path"] == target_source_params["directory_path"]
        assert params["file_format"] == expected_file_formats[params["file_format"]["type"]]
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
        {
            "type": "s3",
            "directory_path": "some/path",
            "file_format": {
                "type": "excel",
                "include_header": True,
            },
        },
        {
            "type": "s3",
            "directory_path": "some/path",
            "file_format": {
                "type": "xml",
                "root_tag": "data",
                "row_tag": "record",
            },
        },
        {
            "type": "s3",
            "directory_path": "some/path",
            "file_format": {
                "type": "orc",
            },
        },
        {
            "type": "s3",
            "directory_path": "some/path",
            "file_format": {
                "type": "parquet",
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
    "target_source_params, target_params, expected_errors",
    [
        pytest.param(
            {
                "type": "s3",
                "directory_path": "/some/path",
                "file_format": {
                    "type": "excel",
                    "include_header": True,
                },
            },
            {
                "file_name_template": "{run_created_at}",
            },
            [
                {
                    "context": {},
                    "input": "{run_created_at}",
                    "location": ["body", "target_params", "s3", "file_name_template"],
                    "message": "Value error, Missing required placeholders: extension, index",
                    "code": "value_error",
                },
            ],
            id="missing_required_placeholders",
        ),
        pytest.param(
            {
                "type": "s3",
                "directory_path": "/some/path",
                "file_format": {
                    "type": "xml",
                    "root_tag": "data",
                    "row_tag": "record",
                },
            },
            {
                "file_name_template": "{run_created_at}_{index}.{extension}{some_unknown_tag}",
            },
            [
                {
                    "context": {},
                    "input": "{run_created_at}_{index}.{extension}{some_unknown_tag}",
                    "location": ["body", "target_params", "s3", "file_name_template"],
                    "message": "Value error, Invalid placeholder: 'some_unknown_tag'",
                    "code": "value_error",
                },
            ],
            id="unknown_tag",
        ),
        pytest.param(
            {
                "type": "s3",
                "directory_path": "/some/path",
                "file_format": {
                    "type": "xml",
                    "root_tag": "data",
                    "row_tag": "record",
                },
            },
            {
                "file_name_template": "{run_created_at}:{index}.{extension}",
            },
            [
                {
                    "context": {},
                    "input": "{run_created_at}:{index}.{extension}",
                    "location": ["body", "target_params", "s3", "file_name_template"],
                    "message": "Value error, Template contains invalid characters. Allowed: letters, numbers, '.', '_', '-', '{', '}'",
                    "code": "value_error",
                },
            ],
            id="prohibited_symbol",
        ),
        pytest.param(
            {
                "type": "s3",
                "directory_path": "/some/path",
                "file_format": {
                    "type": "excel",
                    "include_header": True,
                },
            },
            {
                "file_name_template": "{index}.{extension}",
            },
            [
                {
                    "context": {},
                    "input": "{index}.{extension}",
                    "location": ["body", "target_params", "s3", "file_name_template"],
                    "message": "Value error, At least one of placeholders must be present: {run_id} or {run_created_at}",
                    "code": "value_error",
                },
            ],
            id="missing_placeholders",
        ),
    ],
)
async def test_file_name_template_validation(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    group_queue: Queue,
    mock_group: MockGroup,
    target_source_params: dict,
    target_params: dict,
    expected_errors: list,
    create_connection_data: dict,
):
    first_connection, second_connection = two_group_connections
    user = mock_group.get_member_of_role(UserTestRoles.Developer)

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
            "target_params": {**target_source_params, **target_params},
            "strategy_params": {"type": "full"},
            "queue_id": group_queue.id,
        },
    )

    assert result.status_code == 422
    assert result.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": expected_errors,
        },
    }
