import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.utils import MockConnection, MockGroup, MockUser

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_change_owner_of_connection(
    client: AsyncClient,
    user_connection: MockConnection,
    simple_user: MockUser,
    group_connection: MockConnection,
):
    for connection in user_connection, group_connection:
        result = await client.post(
            f"v1/connections/{connection.id}/change_owner",
            json={
                "new_user_id": simple_user.id,
            },
        )
        assert result.status_code == 401
        assert result.json() == {
            "ok": False,
            "status_code": 401,
            "message": "Not authenticated",
        }


async def test_simple_user_cannot_change_owner_of_connection(
    client: AsyncClient,
    user_connection: MockConnection,
    group_connection: MockConnection,
    simple_user: MockUser,
):
    for connection in user_connection, group_connection:
        result = await client.post(
            f"v1/connections/{connection.id}/change_owner",
            headers={"Authorization": f"Bearer {simple_user.token}"},
            json={
                "new_user_id": simple_user.id,
            },
        )
        assert result.status_code == 404
        assert result.json() == {
            "ok": False,
            "status_code": 404,
            "message": "Connection not found",
        }


async def test_group_member_cannot_change_owner_of_connection(
    client: AsyncClient,
    user_connection: MockConnection,
    group_connection: MockConnection,
):
    member = group_connection.owner_group.members[0]
    for connection in user_connection, group_connection:
        result = await client.post(
            f"v1/connections/{connection.id}/change_owner",
            headers={"Authorization": f"Bearer {member.token}"},
            json={
                "new_user_id": member.id,
            },
        )
        assert result.status_code == 404
        assert result.json() == {
            "ok": False,
            "status_code": 404,
            "message": "Connection not found",
        }


async def test_group_admin_cannot_change_owner_of_user_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    user_connection: MockConnection,
    simple_user: MockUser,
):
    admin = group_connection.owner_group.admin
    result = await client.post(
        f"v1/connections/{user_connection.id}/change_owner",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={
            "new_user_id": simple_user.id,
        },
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


async def test_admin_can_change_owner_of_group_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    simple_user: MockUser,
    session: AsyncSession,
):
    admin = group_connection.owner_group.admin
    result = await client.post(
        f"v1/connections/{group_connection.id}/change_owner",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={
            "new_user_id": simple_user.id,
        },
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Owner was changed",
    }
    await session.refresh(group_connection.connection)
    assert group_connection.connection.user_id == simple_user.id
    assert group_connection.connection.group_id is None


async def test_other_admin_cannot_change_owner_of_group_connection(
    client: AsyncClient, group_connection: MockConnection, empty_group: MockGroup
):
    result = await client.post(
        f"v1/connections/{group_connection.id}/change_owner",
        headers={"Authorization": f"Bearer {empty_group.admin.token}"},
        json={
            "new_user_id": empty_group.admin.id,
        },
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


async def test_superuser_can_change_owner_of_user_connection(
    client: AsyncClient,
    user_connection: MockConnection,
    superuser: MockUser,
    empty_group: MockGroup,
    session: AsyncSession,
):
    result = await client.post(
        f"v1/connections/{user_connection.id}/change_owner",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": empty_group.id,
        },
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Owner was changed",
    }
    await session.refresh(user_connection.connection)
    assert user_connection.connection.user_id is None
    assert user_connection.connection.group_id == empty_group.id


async def test_superuser_can_change_owner_of_group_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    superuser: MockUser,
    empty_group: MockGroup,
    session: AsyncSession,
):
    result = await client.post(
        f"v1/connections/{group_connection.id}/change_owner",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": empty_group.id,
        },
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Owner was changed",
    }
    await session.refresh(group_connection.connection)
    assert group_connection.connection.user_id is None
    assert group_connection.connection.group_id == empty_group.id
