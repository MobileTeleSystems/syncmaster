import pytest

from syncmaster.config import Settings
from syncmaster.scheduler.transfer_fetcher import TransferFetcher


@pytest.fixture
def transfer_fetcher(settings: Settings) -> TransferFetcher:
    return TransferFetcher(settings)
