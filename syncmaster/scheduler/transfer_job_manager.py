# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from kombu.exceptions import KombuError

from syncmaster.backend.services.unit_of_work import UnitOfWork
from syncmaster.db.models import RunType, Status, Transfer
from syncmaster.exceptions.run import CannotConnectToTaskQueueError
from syncmaster.scheduler.settings import SchedulerAppSettings as Settings
from syncmaster.scheduler.utils import get_async_session
from syncmaster.schemas.v1.connections.connection import ReadAuthDataSchema
from syncmaster.worker import celery


class TransferJobManager:
    def __init__(self, settings: Settings):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_jobstore("sqlalchemy", url=settings.database.sync_url)
        self.settings = settings

    def update_jobs(self, transfers: list[Transfer]) -> None:
        for transfer in transfers:
            job_id = str(transfer.id)
            existing_job = self.scheduler.get_job(job_id)

            if not transfer.is_scheduled or transfer.is_deleted:
                if existing_job:
                    self.scheduler.remove_job(job_id)
                continue

            if existing_job:
                self.scheduler.modify_job(
                    job_id=job_id,
                    trigger=CronTrigger.from_crontab(transfer.schedule),
                    misfire_grace_time=self.settings.scheduler.MISFIRE_GRACE_TIME_SECONDS,
                    args=(transfer.id,),
                )
            else:
                self.scheduler.add_job(
                    func=TransferJobManager.send_job_to_celery,
                    id=job_id,
                    trigger=CronTrigger.from_crontab(transfer.schedule),
                    misfire_grace_time=self.settings.scheduler.MISFIRE_GRACE_TIME_SECONDS,
                    args=(transfer.id,),
                )

    @staticmethod
    async def send_job_to_celery(transfer_id: int) -> None:
        """
        Do not pass additional arguments like settings,
        otherwise they will be serialized in jobs table.
        """
        settings = Settings()

        async with get_async_session(settings) as session:
            unit_of_work = UnitOfWork(session=session, settings=settings)

            transfer = await unit_of_work.transfer.read_by_id(transfer_id)
            credentials_source = await unit_of_work.credentials.read(transfer.source_connection_id)
            credentials_target = await unit_of_work.credentials.read(transfer.target_connection_id)

            async with unit_of_work:
                run = await unit_of_work.run.create(
                    transfer_id=transfer_id,
                    source_creds=ReadAuthDataSchema(auth_data=credentials_source).dict(),
                    target_creds=ReadAuthDataSchema(auth_data=credentials_target).dict(),
                    type=RunType.SCHEDULED,
                )

            try:
                await asyncio.to_thread(
                    celery.send_task,
                    "run_transfer_task",
                    kwargs={"run_id": run.id},
                    queue=transfer.queue.name,
                )
            except KombuError as e:
                async with unit_of_work:
                    await unit_of_work.run.update(run_id=run.id, status=Status.FAILED)
                raise CannotConnectToTaskQueueError(run_id=run.id) from e
