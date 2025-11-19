import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Group
from tests.mocks import MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_only_superuser_can_delete_group(
    client: AsyncClient,
    empty_group: MockGroup,
    superuser: MockUser,
    session: AsyncSession,
):
    g_id = empty_group.group.id

    response = await client.delete(
        f"v1/groups/{empty_group.id}",
        headers={
            "Authorization": f"Bearer {superuser.token}",
        },
    )
    assert response.status_code == 204, response.text

    session.expunge_all()
    group_in_db = await session.get(Group, g_id)
    assert group_in_db is None


async def test_not_superuser_cannot_delete_group(
    client: AsyncClient,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_guest_plus)

    response = await client.delete(
        f"v1/groups/{group.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }
    assert response.status_code == 403, response.text


async def test_not_authorized_user_cannot_delete_group(client: AsyncClient, empty_group: MockGroup):
    response = await client.delete(f"v1/groups/{empty_group.id}")
    assert response.status_code == 401, response.text
    assert response.json() == {
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
    response = await client.delete(
        "v1/groups/-1",
        headers={
            "Authorization": f"Bearer {simple_user.token}",
        },
    )
    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }
    assert response.status_code == 403, response.text


async def test_superuser_cannot_delete_unknown_group_error(
    client: AsyncClient,
    superuser: MockUser,
):
    response = await client.delete(
        "v1/groups/-1",
        headers={
            "Authorization": f"Bearer {superuser.token}",
        },
    )
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert response.status_code == 404, response.text
