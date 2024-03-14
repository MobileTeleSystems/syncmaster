# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from typing import get_args

import pytest
from backend.api.v1.connections import CONNECTION_TYPES
from httpx import AsyncClient

from tests.utils import MockUser

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_unauthorized_user_cannot_read_connection_types(client: AsyncClient):
    # Act
    result = await client.get("v1/connections/known_types")
    # Assert
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_groupless_user_can_read_connection_types(client: AsyncClient, simple_user: MockUser):
    # Act
    result = await client.get(
        "v1/connections/known_types",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    # Assert
    assert result.status_code == 200
    assert set(result.json()) == {get_args(type)[0] for type in CONNECTION_TYPES}
