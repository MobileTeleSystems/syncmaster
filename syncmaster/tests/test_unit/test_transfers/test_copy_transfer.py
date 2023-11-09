from operator import or_

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockConnection, MockGroup, MockTransfer, MockUser

from app.db.models import Connection

pytestmark = [pytest.mark.asyncio]


# TODO: implent tests for: from group to same group
async def test_group_member_can_copy_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    empty_group: MockGroup,
    session: AsyncSession,
    request,
    event_loop,
):
    # Arrange
    user = group_transfer.owner_group.admin
    await client.post(
        f"v1/groups/{empty_group.id}/users/{user.user.id}",
        headers={"Authorization": f"Bearer {empty_group.admin.token}"},
    )

    # Act
    result_response = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "remove_source": False,
            "new_group_id": empty_group.id,
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


async def test_group_member_can_not_copy_transfer_with_remove_source(
    client: AsyncClient,
    group_transfer: MockTransfer,
    empty_group: MockGroup,
    session: AsyncSession,
    event_loop,
):
    # Arrange
    user = group_transfer.owner_group.members[0]
    await client.post(
        f"v1/groups/{empty_group.id}/users/{user.user.id}",
        headers={"Authorization": f"Bearer {empty_group.admin.token}"},
    )

    # Act
    result_response = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "remove_source": True,
            "new_group_id": empty_group.id,
        },
    )

    # Assert
    result_json = result_response.json()
    assert result_response.status_code == 403
    assert result_json == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }


async def test_group_admin_can_copy_transfer_with_remove_source_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    empty_group: MockGroup,
    session: AsyncSession,
    request,
    event_loop,
):
    # Arrange
    user = group_transfer.owner_group.admin
    await client.post(
        f"v1/groups/{empty_group.id}/users/{user.user.id}",
        headers={"Authorization": f"Bearer {empty_group.admin.token}"},
    )

    # Act
    result_response = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "remove_source": True,
            "new_group_id": empty_group.id,
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

    source_transfer_response = await client.get(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert source_transfer_response.json()["status_code"] == 404
    assert source_transfer_response.json()["message"] == "Transfer not found"

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


async def test_copy_transfer_with_non_existing_recipient_group_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    session: AsyncSession,
):
    # Arrange
    admin = group_transfer.owner_group.admin
    # Act
    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={
            "remove_source": False,
            "new_group_id": -1,
        },
    )

    assert result.status_code == 404
    assert result.json()["message"] == "Group not found"


async def test_copy_non_existing_transfer_error(
    client: AsyncClient,
    session: AsyncSession,
    group_transfer: MockTransfer,
    empty_group: MockGroup,
):
    # Arrnage
    user = group_transfer.owner_group.admin
    await client.post(
        f"v1/groups/{empty_group.id}/users/{user.user.id}",
        headers={"Authorization": f"Bearer {empty_group.admin.token}"},
    )

    # Act
    result = await client.post(
        "v1/transfers/-1/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "remove_source": False,
            "new_group_id": empty_group.id,
        },
    )

    # Assert
    assert result.status_code == 404
    assert result.json()["message"] == "Transfer not found"


async def test_groupless_user_can_not_copy_transfer_error(
    client: AsyncClient,
    session: AsyncSession,
    simple_user: MockUser,
    group_transfer: MockTransfer,
    empty_group: MockGroup,
):
    # Act
    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "remove_source": False,
            "new_group_id": empty_group.id,
        },
    )

    # Assert
    assert result.status_code == 404
    assert result.json()["message"] == "Transfer not found"


async def test_other_group_member_can_not_copy_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    group_connection: MockConnection,
    session: AsyncSession,
    event_loop,
):
    # Arrange
    group_member = group_connection.owner_group.members[0]

    # Act
    result_response = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {group_member.token}"},
        json={
            "remove_source": True,
            "new_group_id": group_connection.owner_group.group.id,
        },
    )

    # Assert
    result_json = result_response.json()
    assert result_response.status_code == 404
    assert result_json == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }
