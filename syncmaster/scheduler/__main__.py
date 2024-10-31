# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import asyncio

from syncmaster.config import Settings
from syncmaster.scheduler.transfer_fetcher import TransferFetcher
from syncmaster.scheduler.transfer_job_manager import TransferJobManager
from syncmaster.scheduler.utils import TRANSFER_FETCHING_TIMEOUT


async def main():
    settings = Settings()
    transfer_fetcher = TransferFetcher(settings)
    transfer_job_manager = TransferJobManager(settings)
    transfer_job_manager.scheduler.start()

    while True:
        transfers = await transfer_fetcher.fetch_updated_jobs()
        if transfers:
            transfer_job_manager.update_jobs(transfers)
            transfer_fetcher.last_updated_at = max(t.updated_at for t in transfers)
        await asyncio.sleep(TRANSFER_FETCHING_TIMEOUT)


if __name__ == "__main__":
    asyncio.run(main())
