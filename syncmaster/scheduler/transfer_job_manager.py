# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from kombu.exceptions import KombuError
from sqlalchemy import any_, select

from syncmaster.db.models import RunType, Status, Transfer
from syncmaster.exceptions.run import CannotConnectToTaskQueueError
from syncmaster.exceptions.transfer import TransferNotFoundError
from syncmaster.scheduler.celery import app as celery
from syncmaster.scheduler.settings import SchedulerAppSettings as Settings
from syncmaster.scheduler.utils import get_async_engine, get_async_session
from syncmaster.schemas.v1.connections.connection_base import ReadAuthDataSchema
from syncmaster.server.services.unit_of_work import UnitOfWork


class TransferJobManager:
    def __init__(self, settings: Settings):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_jobstore("sqlalchemy", url=settings.database.sync_url)
        self.settings = settings

    def update_jobs(self, transfers: list[Transfer]) -> None:
        for transfer in transfers:
            job_id = str(transfer.id)
            existing_job = self.scheduler.get_job(job_id)

            if not transfer.is_scheduled:
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

    async def remove_orphan_jobs(self) -> None:
        all_jobs = self.scheduler.get_jobs()
        job_transfer_ids = [int(job.id) for job in all_jobs]

        async with get_async_engine(self.settings) as engine, get_async_session(engine) as session:
            result = await session.execute(
                select(Transfer).where(Transfer.id == any_(job_transfer_ids)),  # type: ignore[arg-type]
            )
            existing_transfers = result.scalars().all()
            existing_transfer_ids = {t.id for t in existing_transfers}

        missing_job_ids = set(job_transfer_ids) - existing_transfer_ids
        for job_id in missing_job_ids:
            self.scheduler.remove_job(str(job_id))

    @staticmethod
    async def send_job_to_celery(transfer_id: int) -> None:  # noqa: WPS602, WPS217
        """
        1. Do not pass additional arguments like settings,
        otherwise they will be serialized in jobs table.
        2. Instance methods are bound to specific objects and cannot be reliably serialized
        due to the weak reference problem. Use a static method instead, as it is not
        object-specific and can be serialized.
        """
        settings = Settings()

        async with get_async_engine(settings) as engine, get_async_session(engine) as session:
            unit_of_work = UnitOfWork(session=session, settings=settings)

            try:
                transfer = await unit_of_work.transfer.read_by_id(transfer_id)
            except TransferNotFoundError:
                return

            credentials_source = await unit_of_work.credentials.read(transfer.source_connection_id)
            credentials_target = await unit_of_work.credentials.read(transfer.target_connection_id)

            async with unit_of_work:
                run = await unit_of_work.run.create(
                    transfer_id=transfer_id,
                    source_creds=ReadAuthDataSchema(auth_data=credentials_source).model_dump(),
                    target_creds=ReadAuthDataSchema(auth_data=credentials_target).model_dump(),
                    type=RunType.SCHEDULED,
                )

            try:
                await asyncio.to_thread(
                    celery.send_task,
                    "run_transfer_task",
                    kwargs={"run_id": run.id},
                    queue=transfer.queue.slug,
                )
            except KombuError as e:
                async with unit_of_work:
                    await unit_of_work.run.update(run_id=run.id, status=Status.FAILED)
                raise CannotConnectToTaskQueueError(run_id=run.id) from e
