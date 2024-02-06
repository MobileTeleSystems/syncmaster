import pytest
from httpx import AsyncClient
from tests.utils import MockTransfer, UserTestRoles

pytestmark = [pytest.mark.asyncio]


@pytest.mark.parametrize(
    "create_transfer_data",
    [
        {
            "type": "s3",
            "directory_path": "/some/pure/path",
            "file_format": {
                "delimiter": ",",
                "encoding": "utf-8",
                "escape": "\\",
                "header": False,
                "line_sep": "\n",
                "quote": '"',
                "type": "csv",
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
async def test_user_plus_can_update_s3_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_user_plus: UserTestRoles,
    create_connection_data: dict,
    create_transfer_data: dict,
):
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_user_plus)

    # Act
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "source_params": {
                "type": "s3",
                "directory_path": "/some/new/test/directory",
                "file_format": {"type": "jsonline"},
            }
        },
    )

    # Pre-Assert
    source_params = group_transfer.source_params
    source_params.update(
        {
            "directory_path": "/some/new/test/directory",
            "file_format": {
                "encoding": "utf-8",
                "line_sep": "\n",
                "type": "jsonline",
            },
        }
    )
    # Assert
    assert result.status_code == 200
    assert result.json() == {
        "id": group_transfer.id,
        "group_id": group_transfer.group_id,
        "name": group_transfer.transfer.name,
        "description": group_transfer.description,
        "schedule": group_transfer.schedule,
        "is_scheduled": group_transfer.is_scheduled,
        "source_connection_id": group_transfer.source_connection_id,
        "target_connection_id": group_transfer.target_connection_id,
        "source_params": source_params,
        "target_params": group_transfer.target_params,
        "strategy_params": group_transfer.strategy_params,
        "queue_id": group_transfer.transfer.queue_id,
    }
