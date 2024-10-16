import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Group
from tests.mocks import MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_only_superuser_can_delete_group(
    client: AsyncClient,
    empty_group: MockGroup,
    superuser: MockUser,
    session: AsyncSession,
):
    # Arrange
    group = await session.get(Group, empty_group.group.id)
    assert not group.is_deleted

    # Act
    result = await client.delete(
        f"v1/groups/{empty_group.id}",
        headers={
            "Authorization": f"Bearer {superuser.token}",
        },
    )
    # Assert
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Group was deleted",
    }

    await session.refresh(group)
    assert group.is_deleted


async def test_not_superuser_cannot_delete_group(
    client: AsyncClient,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.delete(
        f"v1/groups/{group.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    # Assert
    assert result.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }
    assert result.status_code == 403


async def test_not_authorized_user_cannot_delete_group(client: AsyncClient, empty_group: MockGroup):
    # Arrange
    result = await client.delete(f"v1/groups/{empty_group.id}")
    # Assert
    assert result.status_code == 401
    assert result.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_groupless_user_cannot_delete_group(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
):
    # Act
    result = await client.delete(
        "v1/groups/-1",
        headers={
            "Authorization": f"Bearer {simple_user.token}",
        },
    )
    # Assert
    assert result.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }
    assert result.status_code == 403


async def test_superuser_cannot_delete_unknown_group_error(
    client: AsyncClient,
    superuser: MockUser,
):
    # Act
    result = await client.delete(
        "v1/groups/-1",
        headers={
            "Authorization": f"Bearer {superuser.token}",
        },
    )
    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert result.status_code == 404
