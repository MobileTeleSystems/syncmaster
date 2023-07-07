from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import AsyncClient

from app.main import get_application


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator:
    app = get_application()
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
