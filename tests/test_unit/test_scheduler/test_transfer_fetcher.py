from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.scheduler.transfer_fetcher import TransferFetcher
from tests.mocks import MockTransfer

pytestmark = [pytest.mark.asyncio, pytest.mark.scheduler]


async def test_fetch_jobs_without_last_updated_at(
    session: AsyncSession,
    transfer_fetcher: TransferFetcher,
    group_transfers: list[MockTransfer],
):
    transfer_fetcher.last_updated_at = None

    fetched_transfers = await transfer_fetcher.fetch_updated_jobs()

    assert len(fetched_transfers) == len(group_transfers)
    assert {t.id for t in fetched_transfers} == {t.transfer.id for t in group_transfers}


async def test_fetch_jobs_with_outdated_last_updated_at(
    session: AsyncSession,
    transfer_fetcher: TransferFetcher,
    group_transfers: list[MockTransfer],
):
    transfer_fetcher.last_updated_at = datetime.now(tz=UTC) - timedelta(days=1)
    wanted_transfers = [t for t in group_transfers if t.transfer.updated_at > transfer_fetcher.last_updated_at]

    fetched_transfers = await transfer_fetcher.fetch_updated_jobs()

    assert len(fetched_transfers) == len(wanted_transfers)
    assert {t.id for t in fetched_transfers} == {t.transfer.id for t in wanted_transfers}


async def test_fetch_jobs_with_up_to_date_last_updated_at(
    session: AsyncSession,
    transfer_fetcher: TransferFetcher,
    group_transfers: list[MockTransfer],
):
    transfer_fetcher.last_updated_at = datetime.now(tz=UTC)

    fetched_transfers = await transfer_fetcher.fetch_updated_jobs()

    assert not fetched_transfers
