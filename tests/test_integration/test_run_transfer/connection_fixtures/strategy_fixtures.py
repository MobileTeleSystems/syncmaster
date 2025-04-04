import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Transfer


@pytest.fixture
def full_strategy():
    return {
        "type": "full",
    }


@pytest.fixture
def incremental_strategy_by_file_modified_since():
    return {
        "type": "incremental",
        "increment_by": "file_modified_since",
    }


@pytest.fixture
def incremental_strategy_by_file_name():
    return {
        "type": "incremental",
        "increment_by": "file_name",
    }


@pytest.fixture
def incremental_strategy_by_number_column():
    return {
        "type": "incremental",
        "increment_by": "NUMBER",
    }


@pytest_asyncio.fixture
async def update_transfer_strategy(session: AsyncSession, request: pytest.FixtureRequest):
    async def _update_transfer_strategy(transfer: Transfer, strategy_fixture_name: str) -> None:
        strategy = request.getfixturevalue(strategy_fixture_name)
        transfer.strategy_params = strategy
        await session.commit()
        return transfer

    return _update_transfer_strategy
