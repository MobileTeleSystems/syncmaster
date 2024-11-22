import pytest

from syncmaster.backend.settings import ServerAppSettings as Settings
from syncmaster.scheduler.transfer_fetcher import TransferFetcher


@pytest.fixture
def transfer_fetcher(settings: Settings) -> TransferFetcher:
    return TransferFetcher(settings)
