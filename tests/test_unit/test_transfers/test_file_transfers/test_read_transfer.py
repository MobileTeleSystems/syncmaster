import pytest
from httpx import AsyncClient

from tests.mocks import MockTransfer, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


@pytest.mark.parametrize(
    "create_transfer_data",
    [
        {
            "source_and_target_params": {
                "type": "s3",
                "directory_path": "/some/pure/path",
                "file_format": {
                    "delimiter": ",",
                    "encoding": "utf-8",
                    "escape": "\\",
                    "include_header": False,
                    "line_sep": "\n",
                    "quote": '"',
                    "type": "csv",
                    "compression": "gzip",
                },
                "options": {},
            },
            "target_params": {
                "file_name_template": "{run_created_at}_{index}.{extension}",
            },
            "transformations": [
                {
                    "type": "dataframe_rows_filter",
                    "filters": [
                        {
                            "type": "not_equal",
                            "field": "col1",
                            "value": "something",
                        },
                        {
                            "type": "less_than",
                            "field": "col2",
                            "value": "20",
                        },
                    ],
                },
            ],
        },
        {
            "source_and_target_params": {
                "type": "s3",
                "directory_path": "/some/excel/path",
                "file_format": {
                    "type": "excel",
                    "include_header": True,
                    "start_cell": "A1",
                },
                "options": {},
            },
            "target_params": {
                "file_name_template": "{index}.{extension}",
            },
        },
        {
            "source_and_target_params": {
                "type": "s3",
                "directory_path": "/some/xml/path",
                "file_format": {
                    "type": "xml",
                    "root_tag": "data",
                    "row_tag": "record",
                    "compression": "bzip2",
                },
                "options": {},
            },
            "target_params": {
                "file_name_template": "{run_created_at}-{index}.{extension}",
            },
        },
        {
            "source_and_target_params": {
                "type": "s3",
                "directory_path": "/some/orc/path",
                "file_format": {
                    "type": "orc",
                    "compression": "zlib",
                },
                "options": {},
            },
            "target_params": {
                "file_name_template": "{run_created_at}_{index}.{extension}",
            },
        },
        {
            "source_and_target_params": {
                "type": "s3",
                "directory_path": "/some/parquet/path",
                "file_format": {
                    "type": "parquet",
                    "compression": "lz4",
                },
                "options": {},
            },
            "target_params": {
                "file_name_template": "{run_created_at}_{index}.{extension}",
            },
        },
    ],
)
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
async def test_guest_plus_can_read_s3_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_guest_plus: UserTestRoles,
    create_connection_data: dict,
    create_transfer_data: dict,
):
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.get(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    # Assert
    assert result.json() == {
        "id": group_transfer.id,
        "group_id": group_transfer.group_id,
        "name": group_transfer.name,
        "description": group_transfer.description,
        "schedule": group_transfer.schedule,
        "is_scheduled": group_transfer.is_scheduled,
        "source_connection_id": group_transfer.source_connection_id,
        "target_connection_id": group_transfer.target_connection_id,
        "source_params": group_transfer.source_params,
        "target_params": group_transfer.target_params,
        "strategy_params": group_transfer.strategy_params,
        "transformations": group_transfer.transformations,
        "queue_id": group_transfer.transfer.queue_id,
    }
    assert result.status_code == 200
