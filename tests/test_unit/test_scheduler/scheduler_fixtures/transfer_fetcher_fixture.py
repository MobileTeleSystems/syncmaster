import pytest

from syncmaster.scheduler.transfer_fetcher import TransferFetcher
from syncmaster.settings import Settings


@pytest.fixture
def transfer_fetcher(settings: Settings) -> TransferFetcher:
    return TransferFetcher(settings)
