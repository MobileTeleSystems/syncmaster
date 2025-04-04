import pytest
from httpx import AsyncClient

from tests.mocks import MockTransfer, UserTestRoles
from tests.test_unit.utils import build_transfer_json

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
                "file_name_template": "{run_id}-{index}.{extension}",
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
            "strategy_params": {
                "type": "incremental",
                "increment_by": "file_modified_since",
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
    user = group_transfer.owner_group.get_member_of_role(role_guest_plus)

    result = await client.get(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert result.status_code == 200, result.json()
    assert result.json() == build_transfer_json(group_transfer)
