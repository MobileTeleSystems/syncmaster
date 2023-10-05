import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_unit.utils import create_acl, create_connection
from tests.utils import MockGroup, MockUser

from app.db.models import ObjectType, Rule

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_get_group_rules(
    client: AsyncClient, empty_group: MockGroup
) -> None:
    result = await client.get(f"v1/groups/{empty_group.id}/rules")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_simple_user_cannot_get_group_rules(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
) -> None:
    result = await client.get(
        f"v1/groups/{empty_group.id}/rules",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }


async def test_group_member_cannot_get_group_rules(
    client: AsyncClient,
    not_empty_group: MockGroup,
) -> None:
    result = await client.get(
        f"v1/groups/{not_empty_group.id}/rules",
        headers={"Authorization": f"Bearer {not_empty_group.members[0].token}"},
    )
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }


async def test_group_admin_and_superuser_can_get_group_rules(
    client: AsyncClient,
    not_empty_group: MockGroup,
    superuser: MockUser,
    session: AsyncSession,
) -> None:
    answer = {
        "meta": {
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "page": 1,
            "page_size": 20,
            "pages": 1,
            "previous_page": None,
            "total": 0,
        },
        "items": [],
    }
    for user in not_empty_group.admin, superuser:
        result = await client.get(
            f"v1/groups/{not_empty_group.id}/rules",
            headers={"Authorization": f"Bearer {user.token}"},
        )
        assert result.status_code == 200
        assert result.json() == answer

    connection = await create_connection(
        session=session,
        name="test_read_acl",
        group_id=not_empty_group.id,
    )

    acl = await create_acl(
        session=session,
        object_id=connection.id,
        object_type=ObjectType.CONNECTION,
        user_id=not_empty_group.members[0].id,
        rule=Rule.WRITE,
    )
    for user in not_empty_group.admin, superuser:
        result = await client.get(
            f"v1/groups/{not_empty_group.id}/rules",
            headers={"Authorization": f"Bearer {user.token}"},
        )
        assert result.status_code == 200
        assert result.json() == {
            "meta": {
                "has_next": False,
                "has_previous": False,
                "next_page": None,
                "page": 1,
                "page_size": 20,
                "pages": 1,
                "previous_page": None,
                "total": 1,
            },
            "items": [
                {
                    "object_id": connection.id,
                    "object_type": ObjectType.CONNECTION.value,
                    "rule": Rule.WRITE.value,
                    "user_id": not_empty_group.members[0].id,
                },
            ],
        }
    await session.delete(acl)
    await session.delete(connection)
    await session.commit()
