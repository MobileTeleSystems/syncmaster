import pytest
from httpx import AsyncClient

from syncmaster.db.models import Queue
from tests.mocks import MockConnection, MockGroup, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


@pytest.mark.parametrize(
    "create_connection_data",
    [
        {
            "type": "postgres",
            "host": "localhost",
            "port": 5432,
        },
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    "target_source_params",
    [
        {
            "type": "postgres",
            "table_name": "table",
        },
    ],
)
async def test_cannot_create_db_transfer_with_short_table_name(
    client: AsyncClient,
    two_group_connections: tuple[MockConnection, MockConnection],
    group_queue: Queue,
    mock_group: MockGroup,
    target_source_params: dict,
    create_connection_data: dict,
):
    first_connection, second_connection = two_group_connections
    user = mock_group.get_member_of_role(UserTestRoles.Developer)

    response = await client.post(
        "v1/transfers",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": mock_group.group.id,
            "name": "new test transfer",
            "source_connection_id": first_connection.id,
            "target_connection_id": second_connection.id,
            "source_params": target_source_params,
            "target_params": target_source_params,
            "queue_id": group_queue.id,
        },
    )

    assert response.status_code == 422, response.text
    assert response.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [
                {
                    "context": {},
                    "input": "table",
                    "location": ["body", "source_params", "postgres", "table_name"],
                    "message": "Value error, Table name should be in format myschema.mytable",
                    "code": "value_error",
                },
                {
                    "context": {},
                    "input": "table",
                    "location": ["body", "target_params", "postgres", "table_name"],
                    "message": "Value error, Table name should be in format myschema.mytable",
                    "code": "value_error",
                },
            ],
        },
    }
