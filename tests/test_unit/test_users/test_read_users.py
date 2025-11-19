import random
import string

import pytest
from httpx import AsyncClient

from tests.mocks import MockUser

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_get_users_unauthorized(client: AsyncClient):
    response = await client.get("v1/users")

    assert response.status_code == 401, response.text
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_get_users_authorized(client: AsyncClient, simple_user: MockUser):
    user = simple_user
    headers = {"Authorization": f"Bearer {simple_user.token}"}

    response = await client.get("v1/users", headers=headers)

    assert response.status_code == 200, response.text
    response = response.json()
    assert response["items"][0].keys() == {"id", "is_superuser", "username"}
    assert response["meta"] == {
        "page": 1,
        "pages": 1,
        "total": len(response["items"]),
        "page_size": 20,
        "has_next": False,
        "has_previous": False,
        "next_page": None,
        "previous_page": None,
    }
    for user_data in response["items"]:
        assert user_data.keys() == {"id", "is_superuser", "username"}
        if user_data["id"] == user.id:
            assert user_data == {
                "id": user.id,
                "username": user.username,
                "is_superuser": user.is_superuser,
            }


async def test_get_users_inactive(client: AsyncClient, inactive_user: MockUser):
    headers = {"Authorization": f"Bearer {inactive_user.token}"}

    response = await client.get("v1/users", headers=headers)

    assert response.status_code == 403, response.text
    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }


@pytest.mark.parametrize(
    "search_value_extractor",
    [
        lambda user: user.username,
        lambda user: user.username + "".join(random.choices(string.ascii_lowercase + string.digits, k=2)),
        lambda user: user.username[:-2],
        lambda user: user.username[:-2] + "".join(random.choices(string.ascii_lowercase + string.digits, k=2)),
    ],
    ids=[
        "search_by_username_full_match",
        "search_by_username_with_additional_symbols",
        "search_by_username_partial_match",
        "search_by_username_fuzzy_match",
    ],
)
async def test_search_users_with_query(
    client: AsyncClient,
    superuser: MockUser,
    simple_user: MockUser,
    search_value_extractor,
):
    user = simple_user
    search_query = search_value_extractor(user)

    response = await client.get(
        "v1/users",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"search_query": search_query},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 1,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [
            {
                "id": user.id,
                "username": user.username,
                "is_superuser": user.is_superuser,
            },
        ],
    }


async def test_search_users_with_nonexistent_query(
    client: AsyncClient,
    superuser: MockUser,
):
    random_search_query = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))

    response = await client.get(
        "v1/users",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"search_query": random_search_query},
    )

    assert response.status_code == 200, response.text
    assert response.json()["items"] == []
