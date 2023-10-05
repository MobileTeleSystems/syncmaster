import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockConnection, MockGroup, MockUser

from app.db.models import Acl, ObjectType, Rule

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_create_rule(
    client: AsyncClient, group_connection: MockConnection
):
    member = group_connection.owner_group.members[0]
    result = await client.post(
        f"v1/connections/{group_connection.id}/rules",
        json={"user_id": member.id, "rule": Rule.WRITE},
    )
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_simple_user_cannot_create_rule_on_group_connection(
    client: AsyncClient, group_connection: MockConnection, simple_user: MockUser
):
    member = group_connection.owner_group.members[0]
    result = await client.post(
        f"v1/connections/{group_connection.id}/rules",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={"user_id": member.id, "rule": Rule.WRITE},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


async def test_group_member_cannot_create_rule_on_group_connection(
    client: AsyncClient, group_connection: MockConnection
):
    member = group_connection.owner_group.members[0]
    result = await client.post(
        f"v1/connections/{group_connection.id}/rules",
        headers={"Authorization": f"Bearer {member.token}"},
        json={"user_id": member.id, "rule": Rule.WRITE},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


async def test_group_admin_can_set_any_rule_on_group_connection(
    client: AsyncClient, group_connection: MockConnection, session: AsyncSession
):
    admin = group_connection.owner_group.admin

    member = group_connection.owner_group.members[0]
    result = await client.post(
        f"v1/connections/{group_connection.id}/rules",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={"user_id": member.id, "rule": Rule.WRITE},
    )
    assert result.status_code == 200
    assert result.json() == {
        "object_id": group_connection.id,
        "object_type": ObjectType.CONNECTION.value,
        "user_id": member.id,
        "rule": Rule.WRITE.value,
    }

    # check that does'nt create new rule for pair object-user
    result = await client.post(
        f"v1/connections/{group_connection.id}/rules",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={"user_id": member.id, "rule": Rule.DELETE},
    )
    assert result.status_code == 200
    assert result.json() == {
        "object_id": group_connection.id,
        "object_type": ObjectType.CONNECTION.value,
        "user_id": member.id,
        "rule": Rule.DELETE.value,
    }

    query = select(Acl).filter_by(
        object_id=group_connection.id,
        object_type=ObjectType.CONNECTION,
        user_id=member.id,
    )
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    assert total == 1

    result = await client.get(
        f"v1/groups/{group_connection.owner_group.id}/rules",
        headers={"Authorization": f"Bearer {admin.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "items": [
            {
                "object_id": group_connection.id,
                "object_type": ObjectType.CONNECTION.value,
                "rule": Rule.DELETE.value,
                "user_id": member.id,
            },
            {
                "object_id": group_connection.id,
                "object_type": ObjectType.CONNECTION.value,
                "rule": Rule.WRITE.value,
                "user_id": group_connection.acls[0].user_id,
            },
            {
                "object_id": group_connection.id,
                "object_type": ObjectType.CONNECTION.value,
                "rule": Rule.DELETE.value,
                "user_id": group_connection.acls[1].user_id,
            },
        ],
        "meta": {
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "page": 1,
            "page_size": 20,
            "pages": 1,
            "previous_page": None,
            "total": 3,
        },
    }


async def test_superuser_can_set_any_rule_on_group_connection(
    client: AsyncClient, group_connection: MockConnection, superuser: MockUser
):
    member = group_connection.owner_group.members[0]
    result = await client.post(
        f"v1/connections/{group_connection.id}/rules",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={"user_id": member.id, "rule": Rule.WRITE},
    )
    assert result.status_code == 200
    assert result.json() == {
        "object_id": group_connection.id,
        "object_type": ObjectType.CONNECTION.value,
        "user_id": member.id,
        "rule": Rule.WRITE.value,
    }

    result = await client.get(
        f"v1/groups/{group_connection.owner_group.id}/rules",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "items": [
            {
                "object_id": group_connection.id,
                "object_type": ObjectType.CONNECTION.value,
                "rule": Rule.WRITE.value,
                "user_id": member.id,
            },
            {
                "object_id": group_connection.id,
                "object_type": ObjectType.CONNECTION.value,
                "rule": Rule.WRITE.value,
                "user_id": group_connection.acls[0].user_id,
            },
            {
                "object_id": group_connection.id,
                "object_type": ObjectType.CONNECTION.value,
                "rule": Rule.DELETE.value,
                "user_id": group_connection.acls[1].user_id,
            },
        ],
        "meta": {
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "page": 1,
            "page_size": 20,
            "pages": 1,
            "previous_page": None,
            "total": 3,
        },
    }


async def test_other_group_admin_cannot_create_rule_on_group_connection(
    client: AsyncClient, group_connection: MockConnection, empty_group: MockGroup
):
    member = group_connection.owner_group.members[0]
    result = await client.post(
        f"v1/connections/{group_connection.id}/rules",
        headers={"Authorization": f"Bearer {empty_group.admin.token}"},
        json={"user_id": member.id, "rule": Rule.WRITE},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


async def test_cannot_set_any_rule_on_user_connection(
    client: AsyncClient,
    user_connection: MockConnection,
    superuser: MockUser,
    simple_user: MockUser,
):
    result = await client.post(
        f"v1/connections/{user_connection.id}/rules",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={"user_id": simple_user.id, "rule": Rule.WRITE},
    )
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }
