# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import asyncio
import logging

from syncmaster.scheduler.transfer_fetcher import TransferFetcher
from syncmaster.scheduler.transfer_job_manager import TransferJobManager
from syncmaster.settings import Settings

logger = logging.getLogger(__name__)


async def main():
    settings = Settings()
    transfer_fetcher = TransferFetcher(settings)
    transfer_job_manager = TransferJobManager(settings)
    transfer_job_manager.scheduler.start()

    while True:
        logger.info("Looking at the transfer table...")
        transfers = await transfer_fetcher.fetch_updated_jobs()

        if transfers:
            logger.info(f"Found {len(transfers)} updated transfers: {transfers}")
            transfer_job_manager.update_jobs(transfers)
            transfer_fetcher.last_updated_at = max(t.updated_at for t in transfers)
            logger.info(f"Scheduler state has been updated. Last updated at: {transfer_fetcher.last_updated_at}")

        await asyncio.sleep(settings.SCHEDULER_TRANSFER_FETCHING_TIMEOUT)


if __name__ == "__main__":
    asyncio.run(main())
