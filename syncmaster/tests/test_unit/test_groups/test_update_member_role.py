import pytest
from httpx import AsyncClient
from tests.utils import MockConnection, MockGroup, TestUserRoles

pytestmark = [pytest.mark.asyncio]


async def test_owner_of_group_can_update_user_role(
    client: AsyncClient,
    group: MockGroup,
):
    result = await client.patch(
        f"v1/groups/{group.id}/users/{group.get_member_of_role(TestUserRoles.User).user.id}",
        headers={"Authorization": f"Bearer {group.get_member_of_role(TestUserRoles.Owner).token}"},
        json={
            "role": TestUserRoles.Maintainer,
        },
    )

    assert result.json() == {"role": TestUserRoles.Maintainer}
    assert result.status_code == 200


async def test_owner_of_group_can_not_update_user_role_with_wrong_role(
    client: AsyncClient,
    group: MockGroup,
):
    result = await client.patch(
        f"v1/groups/{group.id}/users/{group.get_member_of_role(TestUserRoles.User).user.id}",
        headers={"Authorization": f"Bearer {group.get_member_of_role(TestUserRoles.Owner).token}"},
        json={
            "role": "Unknown",
        },
    )

    assert result.json() == {
        "detail": [
            {
                "ctx": {"enum_values": ["Maintainer", "User", "Guest"]},
                "loc": ["body", "role"],
                "msg": "value is not a valid enumeration member; permitted: 'Maintainer', 'User', 'Guest'",
                "type": "type_error.enum",
            }
        ]
    }
    assert result.status_code == 422


@pytest.mark.parametrize(
    "group_member",
    [
        TestUserRoles.User,
        TestUserRoles.Guest,
    ],
)
async def test_not_owner_of_group_can_not_update_user_role(
    client: AsyncClient,
    group: MockGroup,
    group_member: str,
):
    result = await client.patch(
        f"v1/groups/{group.id}/users/{group.get_member_of_role(TestUserRoles.User).user.id}",
        headers={"Authorization": f"Bearer {group.get_member_of_role(group_member).token}"},
        json={
            "role": TestUserRoles.Maintainer,
        },
    )

    assert result.json() == {
        "message": "You have no power here",
        "ok": False,
        "status_code": 403,
    }
    assert result.status_code == 403


async def test_other_group_owner_can_not_update_user_role(
    client: AsyncClient,
    group: MockGroup,
    empty_group: MockGroup,
):
    result = await client.patch(
        f"v1/groups/{group.id}/users/{group.get_member_of_role(TestUserRoles.User).user.id}",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(TestUserRoles.Owner).token}"},
        json={
            "role": TestUserRoles.Maintainer,
        },
    )

    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }
    assert result.status_code == 404


async def test_other_group_member_can_not_update_user_role(
    client: AsyncClient,
    group: MockGroup,
    group_connection: MockConnection,
):
    result = await client.patch(
        f"v1/groups/{group.id}/users/{group.get_member_of_role(TestUserRoles.User).user.id}",
        headers={
            "Authorization": f"Bearer {group_connection.owner_group.get_member_of_role(TestUserRoles.User).token}"
        },
        json={
            "role": TestUserRoles.Maintainer,
        },
    )

    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }
    assert result.status_code == 404
