from operator import or_

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockTransfer, MockUser

from app.db.models import Connection

pytestmark = [pytest.mark.asyncio]


async def test_simple_user_can_copy_transfer(
    client: AsyncClient,
    user_transfer: MockTransfer,
    session: AsyncSession,
    simple_user: MockUser,  # TODO: implent tests for user -> user, user -> group, group -> user, group -> group.
    request,
    event_loop,
):
    # Arrange
    user = user_transfer.owner_user

    # Act
    result_response = await client.post(
        f"v1/transfers/{user_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_user_id": simple_user.id,
            "remove_source": False,
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
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )

    assert copied_transfer_response.status_code == 200

    new_connection_source_response = await client.get(
        f"v1/connections/{result_json['source_connection_id']}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )

    assert (
        new_connection_source_response.json()["connection_data"]
        == user_transfer.source_connection.connection.data
    )
    assert {"type": "postgres", "user": None} == new_connection_source_response.json()[
        "auth_data"
    ]

    new_connection_target_response = await client.get(
        f"v1/connections/{result_json['target_connection_id']}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )

    assert (
        new_connection_target_response.json()["connection_data"]
        == user_transfer.target_connection.connection.data
    )
    assert {"type": "postgres", "user": None} == new_connection_target_response.json()[
        "auth_data"
    ]

    assert (
        copied_transfer_response.json()["source_connection_id"]
        == new_connection_source_response.json()["id"]
    )
    assert (
        copied_transfer_response.json()["target_connection_id"]
        == new_connection_target_response.json()["id"]
    )


async def test_simple_user_can_copy_transfer_remove_source_transfer(
    client: AsyncClient,
    user_transfer: MockTransfer,
    session: AsyncSession,
    simple_user: MockUser,
    request,
    event_loop,
):
    # Arrange
    user = user_transfer.owner_user

    # Act
    result_response = await client.post(
        f"v1/transfers/{user_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_user_id": simple_user.id,
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

    source_transfer_response = await client.get(
        f"v1/transfers/{user_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert source_transfer_response.json()["status_code"] == 404
    assert source_transfer_response.json()["message"] == "Transfer not found"

    copied_transfer_response = await client.get(
        f"v1/transfers/{result_json['copied_transfer_id']}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )

    assert copied_transfer_response.status_code == 200

    new_connection_source_response = await client.get(
        f"v1/connections/{result_json['source_connection_id']}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )

    assert (
        new_connection_source_response.json()["connection_data"]
        == user_transfer.source_connection.connection.data
    )
    assert {"type": "postgres", "user": None} == new_connection_source_response.json()[
        "auth_data"
    ]

    new_connection_target_response = await client.get(
        f"v1/connections/{result_json['target_connection_id']}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )

    assert (
        new_connection_target_response.json()["connection_data"]
        == user_transfer.target_connection.connection.data
    )
    assert {"type": "postgres", "user": None} == new_connection_target_response.json()[
        "auth_data"
    ]

    assert (
        copied_transfer_response.json()["source_connection_id"]
        == new_connection_source_response.json()["id"]
    )
    assert (
        copied_transfer_response.json()["target_connection_id"]
        == new_connection_target_response.json()["id"]
    )


async def test_copy_transfer_with_non_existing_recipient_error(
    client: AsyncClient,
    user_transfer: MockTransfer,
    session: AsyncSession,
):
    simple_user = user_transfer.owner_user

    result = await client.post(
        f"v1/transfers/{user_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "new_user_id": 100500,
            "remove_source": False,
        },
    )

    assert result.status_code == 404
    assert result.json()["message"] == "User not found"


async def test_copy_non_existing_transfer_error(
    client: AsyncClient,
    session: AsyncSession,
    user_transfer: MockTransfer,
    superuser,
):
    simple_user = user_transfer.owner_user

    result = await client.post(
        "v1/transfers/100500/copy_transfer",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "new_user_id": superuser.id,
            "remove_source": False,
        },
    )

    assert result.status_code == 404
    assert result.json()["message"] == "Transfer not found"


async def test_user_not_an_owner_of_the_transfer_error(
    client: AsyncClient,
    user_transfer: MockTransfer,
    session: AsyncSession,
    group_transfer: MockTransfer,
):
    result = await client.post(
        f"v1/transfers/{user_transfer.id}/copy_transfer",
        headers={
            "Authorization": f"Bearer {group_transfer.owner_group.members[0].token}"
        },
        json={
            "new_user_id": group_transfer.owner_group.members[1].id,
            "remove_source": False,
        },
    )

    assert result.status_code == 404
    assert result.json()["message"] == "Transfer not found"


async def test_copy_without_rules_to_delete_error(
    client: AsyncClient,
    session: AsyncSession,
    group_transfer: MockTransfer,
):
    user = group_transfer.owner_group.members[0]

    result = await client.post(
        f"v1/transfers/{group_transfer.id}/copy_transfer",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_user_id": group_transfer.owner_group.members[1].id,
            "remove_source": True,
        },
    )

    assert result.status_code == 404
    assert result.json()["message"] == "Transfer not found"
