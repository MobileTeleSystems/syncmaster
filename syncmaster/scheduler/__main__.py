#!/usr/bin/env python
# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import asyncio
import logging

from syncmaster.scheduler.settings import SchedulerAppSettings as Settings
from syncmaster.scheduler.transfer_fetcher import TransferFetcher
from syncmaster.scheduler.transfer_job_manager import TransferJobManager
from syncmaster.settings.log import setup_logging

logger = logging.getLogger(__name__)


async def main():
    settings = Settings()
    setup_logging(settings.logging.get_log_config_path())
    transfer_fetcher = TransferFetcher(settings)
    transfer_job_manager = TransferJobManager(settings)
    transfer_job_manager.scheduler.start()

    while True:  # noqa: WPS457
        logger.info("Looking at the transfer table...")

        await transfer_job_manager.remove_orphan_jobs()
        transfers = await transfer_fetcher.fetch_updated_jobs()

        if transfers:
            logger.info(
                "Found %d updated transfers with ids: %s",
                len(transfers),
                ", ".join(str(t.id) for t in transfers),
            )
            transfer_job_manager.update_jobs(transfers)

            transfer_fetcher.last_updated_at = max(t.updated_at for t in transfers)
            logger.info("Scheduler state has been updated. Last updated at: %s", transfer_fetcher.last_updated_at)

        await asyncio.sleep(settings.scheduler.TRANSFER_FETCHING_TIMEOUT_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
