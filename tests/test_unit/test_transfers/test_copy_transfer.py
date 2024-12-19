import secrets
from operator import or_

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Connection, Queue
from tests.mocks import MockGroup, MockTransfer, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_maintainer_plus_can_copy_transfer_with_remove_source(
    client: AsyncClient,
    session: AsyncSession,
    request,
    event_loop,
    group_transfer_and_group_maintainer_plus: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    # Arrange
    role = group_transfer_and_group_maintainer_plus
    user = group_transfer.owner_group.get_member_of_role(role)

    # Act
    result_response = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
            "remove_source": True,
        },
    )

    # Assert
    result_json = result_response.json()
    assert result_response.status_code == 200

    def delete_rows():
        async def afin():
            delete_new_connections_query = delete(Connection).where(
                or_(
                    Connection.id == result_json["source_connection_id"],
                    Connection.id == result_json["target_connection_id"],
                ),
            )
            await session.execute(delete_new_connections_query)
            await session.commit()

        event_loop.run_until_complete(afin())

    request.addfinalizer(delete_rows)

    copied_transfer_response = await client.get(
        f"v1/transfers/{result_json['copied_transfer_id']}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert copied_transfer_response.status_code == 200

    new_connection_source_response = await client.get(
        f"v1/connections/{result_json['source_connection_id']}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert new_connection_source_response.json()["connection_data"] == group_transfer.source_connection.connection.data
    assert not new_connection_source_response.json()["auth_data"]

    new_connection_target_response = await client.get(
        f"v1/connections/{result_json['target_connection_id']}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert new_connection_target_response.json()["connection_data"] == group_transfer.target_connection.connection.data
    assert not new_connection_target_response.json()["auth_data"]

    assert copied_transfer_response.json()["source_connection_id"] == new_connection_source_response.json()["id"]
    assert copied_transfer_response.json()["target_connection_id"] == new_connection_target_response.json()["id"]


async def test_developer_plus_can_copy_transfer_without_remove_source(
    client: AsyncClient,
    session: AsyncSession,
    request,
    event_loop,
    group_transfer_and_group_developer_plus: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    # Arrange
    role = group_transfer_and_group_developer_plus
    user = group_transfer.owner_group.get_member_of_role(role)

    # Act
    result_response = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
        },
    )

    # Assert
    result_json = result_response.json()
    assert result_response.status_code == 200

    def delete_rows():
        async def afin():
            delete_new_connections_query = delete(Connection).where(
                or_(
                    Connection.id == result_json["source_connection_id"],
                    Connection.id == result_json["target_connection_id"],
                ),
            )
            await session.execute(delete_new_connections_query)
            await session.commit()

        event_loop.run_until_complete(afin())

    request.addfinalizer(delete_rows)

    copied_transfer_response = await client.get(
        f"v1/transfers/{result_json['copied_transfer_id']}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert copied_transfer_response.status_code == 200

    new_connection_source_response = await client.get(
        f"v1/connections/{result_json['source_connection_id']}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert new_connection_source_response.json()["connection_data"] == group_transfer.source_connection.connection.data
    assert not new_connection_source_response.json()["auth_data"]

    new_connection_target_response = await client.get(
        f"v1/connections/{result_json['target_connection_id']}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert new_connection_target_response.json()["connection_data"] == group_transfer.target_connection.connection.data
    assert not new_connection_target_response.json()["auth_data"]

    assert copied_transfer_response.json()["source_connection_id"] == new_connection_source_response.json()["id"]
    assert copied_transfer_response.json()["target_connection_id"] == new_connection_target_response.json()["id"]


async def test_developer_or_below_cannot_copy_transfer_with_remove_source(
    client: AsyncClient,
    session: AsyncSession,
    event_loop,
    group_transfer_and_group_developer_or_below: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    # Arrange
    role = group_transfer_and_group_developer_or_below
    user = group_transfer.owner_group.get_member_of_role(role)

    # Act
    result_response = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "remove_source": True,
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
        },
    )

    # Assert
    result_json = result_response.json()
    assert result_json == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }
    assert result_response.status_code == 403


async def test_groupless_user_cannot_copy_transfer(
    client: AsyncClient,
    session: AsyncSession,
    simple_user: MockUser,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    # Act
    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
        },
    )

    # Assert
    assert result.status_code == 404
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }


async def test_other_group_guest_plus_member_cannot_copy_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    group: MockGroup,
    session: AsyncSession,
    role_guest_plus: UserTestRoles,
    event_loop,
    group_queue: Queue,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }
    assert result.status_code == 404


async def test_superuser_can_copy_transfer_with_remove_source(
    client: AsyncClient,
    session: AsyncSession,
    request,
    event_loop,
    superuser: MockUser,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    # Act
    result_response = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "remove_source": True,
            "new_queue_id": group_queue.id,
        },
    )

    # Assert
    result_json = result_response.json()
    assert result_response.status_code == 200

    def delete_rows():
        async def afin():
            delete_new_connections_query = delete(Connection).where(
                or_(
                    Connection.id == result_json["source_connection_id"],
                    Connection.id == result_json["target_connection_id"],
                ),
            )
            await session.execute(delete_new_connections_query)
            await session.commit()

        event_loop.run_until_complete(afin())

    request.addfinalizer(delete_rows)

    copied_transfer_response = await client.get(
        f"v1/transfers/{result_json['copied_transfer_id']}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    assert copied_transfer_response.status_code == 200

    new_connection_source_response = await client.get(
        f"v1/connections/{result_json['source_connection_id']}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    assert new_connection_source_response.json()["connection_data"] == group_transfer.source_connection.connection.data
    assert not new_connection_source_response.json()["auth_data"]

    new_connection_target_response = await client.get(
        f"v1/connections/{result_json['target_connection_id']}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    assert new_connection_target_response.json()["connection_data"] == group_transfer.target_connection.connection.data
    assert not new_connection_target_response.json()["auth_data"]

    assert copied_transfer_response.json()["source_connection_id"] == new_connection_source_response.json()["id"]
    assert copied_transfer_response.json()["target_connection_id"] == new_connection_target_response.json()["id"]


async def test_maintainer_plus_can_copy_transfer_with_new_name(
    client: AsyncClient,
    session: AsyncSession,
    event_loop,
    group_transfer_and_group_maintainer_plus: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
    request,
):
    # Arrange
    role = group_transfer_and_group_maintainer_plus
    user = group_transfer.owner_group.get_member_of_role(role)
    new_name = f"{secrets.token_hex(5)}"

    # Act
    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
            "new_name": new_name,
        },
    )

    result_json = result.json()

    def delete_rows():
        async def afin():
            delete_new_connections_query = delete(Connection).where(
                or_(
                    Connection.id == result_json["source_connection_id"],
                    Connection.id == result_json["target_connection_id"],
                ),
            )
            await session.execute(delete_new_connections_query)
            await session.commit()

        event_loop.run_until_complete(afin())

    request.addfinalizer(delete_rows)

    # Assert
    assert result.status_code == 200

    copied_transfer_response = await client.get(
        f"v1/transfers/{result_json['copied_transfer_id']}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert copied_transfer_response.json()["name"] == new_name


async def test_check_validate_copy_transfer_parameter_new_name(
    client: AsyncClient,
    session: AsyncSession,
    event_loop,
    group_transfer_and_group_maintainer_plus: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    # Arrange
    role = group_transfer_and_group_maintainer_plus
    user = group_transfer.owner_group.get_member_of_role(role)
    new_name = ""

    # Act
    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
            "new_name": new_name,
        },
    )

    result.json()

    # Assert
    assert result.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [
                {
                    "context": {"min_length": 1},
                    "input": "",
                    "location": ["body", "new_name"],
                    "message": "String should have at least 1 character",
                    "code": "string_too_short",
                },
            ],
        },
    }


async def test_maintainer_plus_can_not_copy_transfer_with_same_name_in_new_group(
    client: AsyncClient,
    session: AsyncSession,
    event_loop,
    group_transfer_with_same_name_maintainer_plus: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    # Arrange
    role = group_transfer_with_same_name_maintainer_plus
    user = group_transfer.owner_group.get_member_of_role(role)
    new_name = "duplicated_group_transfer"

    # Act
    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
            "new_name": new_name,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "conflict",
            "message": "The transfer name already exists in the target group, please specify a new one",
            "details": None,
        },
    }


async def test_developer_plus_cannot_copy_transfer_if_new_queue_in_another_group(
    client: AsyncClient,
    group_transfer_and_group_maintainer_plus: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
    mock_queue: Queue,
):
    # Arrange
    role = group_transfer_and_group_maintainer_plus
    user = group_transfer.owner_group.get_member_of_role(role)

    # Act
    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": mock_queue.id,
        },
    )

    assert result.json() == {
        "error": {
            "code": "bad_request",
            "message": "Queue should belong to the transfer group",
            "details": None,
        },
    }
    assert result.status_code == 400


async def test_superuser_cannot_copy_unknown_transfer_error(
    client: AsyncClient,
    superuser: MockUser,
    group: MockGroup,
    group_queue: Queue,
):
    # Act
    result_response = await client.post(
        "v1/transfers/-1/copy_transfer",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "remove_source": True,
            "new_queue_id": group_queue.id,
        },
    )

    # Assert
    result_json = result_response.json()
    assert result_json == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }
    assert result_response.status_code == 404


async def test_superuser_cannot_copy_transfer_with_unknown_new_group_error(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    # Act
    result_response = await client.post(
        f"v1/transfers/{group_transfer.transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": -1,
            "remove_source": True,
            "new_queue_id": group_queue.id,
        },
    )

    # Assert
    result_json = result_response.json()
    assert result_json == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert result_response.status_code == 404


async def test_developer_plus_cannot_copy_transfer_with_unknown_new_group_error(
    client: AsyncClient,
    role_developer_plus: UserTestRoles,
    group_transfer_and_group_developer_plus: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    # Arrange
    role = group_transfer_and_group_developer_plus
    user = group_transfer.owner_group.get_member_of_role(role)

    # Act
    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": -1,
            "new_queue_id": group_queue.id,
        },
    )

    assert result.json()["error"]["message"] == "Group not found"
    assert result.status_code == 404


async def test_copy_unknown_transfer_error(
    client: AsyncClient,
    group_transfer_and_group_maintainer_plus: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    # Arrnage
    role = group_transfer_and_group_maintainer_plus
    user = group_transfer.owner_group.get_member_of_role(role)

    # Act
    result = await client.post(
        "v1/transfers/-1/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": group_queue.id,
        },
    )

    # Assert
    assert result.json()["error"]["message"] == "Transfer not found"
    assert result.status_code == 404


async def test_developer_plus_cannot_copy_transfer_with_unknown_new_queue_id_error(
    client: AsyncClient,
    event_loop,
    group_transfer_and_group_developer_plus: str,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    # Arrange
    role = group_transfer_and_group_developer_plus
    user = group_transfer.owner_group.get_member_of_role(role)

    # Act
    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "new_queue_id": -1,
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


async def test_superuser_cannot_copy_transfer_with_unknown_new_queue_id_error(
    client: AsyncClient,
    event_loop,
    superuser: MockUser,
    group_transfer: MockTransfer,
    group_queue: Queue,
):
    # Act
    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": group_queue.group_id,
            "remove_source": True,
            "new_queue_id": -1,
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
