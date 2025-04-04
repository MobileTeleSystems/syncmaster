import pytest

from syncmaster.scheduler.transfer_fetcher import TransferFetcher
from syncmaster.server.settings import ServerAppSettings as Settings


@pytest.fixture
def transfer_fetcher(settings: Settings) -> TransferFetcher:
    return TransferFetcher(settings)
