from operator import or_

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockGroup, MockTransfer, MockUser, TestUserRoles

from app.db.models import Connection

pytestmark = [pytest.mark.asyncio]


async def test_maintainer_plus_can_copy_transfer_with_remove_source(
    client: AsyncClient,
    session: AsyncSession,
    request,
    event_loop,
    group_transfer_and_group_maintainer_plus: str,
    group_transfer: MockTransfer,
    empty_group: MockGroup,
):
    # Arrange
    role = group_transfer_and_group_maintainer_plus
    user = group_transfer.owner_group.get_member_of_role(role)

    # Act
    result_response = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": empty_group.id,
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


async def test_user_plus_can_copy_transfer_without_remove_source(
    client: AsyncClient,
    session: AsyncSession,
    request,
    event_loop,
    group_transfer_and_group_user_plus: str,
    group_transfer: MockTransfer,
    empty_group: MockGroup,
):
    # Arrange
    role = group_transfer_and_group_user_plus
    user = group_transfer.owner_group.get_member_of_role(role)

    # Act
    result_response = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
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


async def test_user_or_below_cannot_copy_transfer_with_remove_source(
    client: AsyncClient,
    session: AsyncSession,
    event_loop,
    group_transfer_and_group_user_or_below: str,
    group_transfer: MockTransfer,
    empty_group: MockGroup,
):
    # Arrange
    role = group_transfer_and_group_user_or_below
    user = group_transfer.owner_group.get_member_of_role(role)

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
    assert result_json == {
        "message": "You have no power here",
        "ok": False,
        "status_code": 403,
    }
    assert result_response.status_code == 403


async def test_groupless_user_cannot_copy_transfer(
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
            "new_group_id": empty_group.id,
        },
    )

    # Assert
    assert result.status_code == 404
    assert result.json()["message"] == "Transfer not found"


async def test_other_group_guest_plus_member_cannot_copy_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    group: MockGroup,
    session: AsyncSession,
    role_guest_plus: TestUserRoles,
    event_loop,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group.group.id,
        },
    )

    # Assert
    result_json = result.json()
    assert result_json == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }
    assert result.status_code == 404


async def test_superuser_can_copy_transfer_with_remove_source(
    client: AsyncClient,
    session: AsyncSession,
    request,
    event_loop,
    superuser: MockUser,
    group_transfer: MockTransfer,
    group: MockGroup,
):
    # Act
    result_response = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": group.id,
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


async def test_superuser_cannot_copy_unknown_transfer_error(
    client: AsyncClient,
    session: AsyncSession,
    superuser: MockUser,
    group: MockGroup,
):
    # Act
    result_response = await client.post(
        "v1/transfers/-1/copy_transfer",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": group.id,
            "remove_source": True,
        },
    )

    # Assert
    result_json = result_response.json()
    assert result_json == {
        "message": "Transfer not found",
        "ok": False,
        "status_code": 404,
    }
    assert result_response.status_code == 404


async def test_superuser_cannot_copy_transfer_with_unknown_new_group_error(
    client: AsyncClient,
    session: AsyncSession,
    superuser: MockUser,
    group_transfer: MockTransfer,
):
    # Act
    result_response = await client.post(
        f"v1/transfers/{group_transfer.transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": -1,
            "remove_source": True,
        },
    )

    # Assert
    result_json = result_response.json()
    assert result_json == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }
    assert result_response.status_code == 404


async def test_copy_transfer_with_unknown_new_group_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    session: AsyncSession,
    role_user_plus: TestUserRoles,
):
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_user_plus)

    # Act
    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": -1,
        },
    )

    assert result.json()["message"] == "Group not found"
    assert result.status_code == 404


async def test_copy_unknown_transfer_error(
    client: AsyncClient,
    session: AsyncSession,
    group_transfer_and_group_maintainer_plus: str,
    group_transfer: MockTransfer,
    empty_group: MockGroup,
):
    # Arrnage
    role = group_transfer_and_group_maintainer_plus
    user = group_transfer.owner_group.get_member_of_role(role)

    # Act
    result = await client.post(
        "v1/transfers/-1/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": empty_group.id,
        },
    )

    # Assert
    assert result.json()["message"] == "Transfer not found"
    assert result.status_code == 404
