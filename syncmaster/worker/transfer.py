# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from datetime import datetime, timezone

from asgi_correlation_id import correlation_id
from asgi_correlation_id.extensions.celery import load_correlation_ids
from celery.signals import after_setup_task_logger
from celery.utils.log import get_task_logger
from jinja2 import Template
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, selectinload

from syncmaster.db.models import AuthData, Run, Status, Transfer
from syncmaster.db.repositories.utils import decrypt_auth_data
from syncmaster.settings.log import setup_logging
from syncmaster.worker.base import WorkerTask
from syncmaster.worker.celery import app as celery
from syncmaster.worker.controller import TransferController
from syncmaster.worker.settings import WorkerAppSettings

logger = get_task_logger(__name__)
load_correlation_ids()


@celery.task(name="run_transfer_task", bind=True, track_started=True)
def run_transfer_task(self: WorkerTask, run_id: int) -> None:
    run_transfer(
        run_id=run_id,
        engine=self.engine,
        settings=self.settings,
    )


def run_transfer(run_id: int, engine: Engine, settings: WorkerAppSettings):
    try:
        with Session(engine, expire_on_commit=False) as session:
            run = session.scalar(
                select(Run)
                .where(
                    Run.id == run_id,
                    Run.status == Status.CREATED,
                )
                .options(
                    selectinload(Run.transfer),
                    selectinload(Run.transfer).selectinload(Transfer.group),
                    selectinload(Run.transfer).selectinload(Transfer.source_connection),
                    selectinload(Run.transfer).selectinload(Transfer.target_connection),
                ),
            )
            if run is None:
                logger.info("Run %r not found or already executed by someone else", run_id)
                return

            source_connection = run.transfer.source_connection
            source_auth_data_query = select(AuthData).where(AuthData.connection_id == run.transfer.source_connection.id)
            source_auth_data_encrypted = session.scalar(source_auth_data_query)
            source_auth_data = decrypt_auth_data(source_auth_data_encrypted.value, settings)

            target_connection = run.transfer.target_connection
            target_auth_data_query = select(AuthData).where(AuthData.connection_id == run.transfer.target_connection.id)
            target_auth_data_encrypted = session.scalar(target_auth_data_query)
            target_auth_data = decrypt_auth_data(target_auth_data_encrypted.value, settings)

            logger.info("Starting run %r", run_id)
            run.status = Status.STARTED
            run.started_at = datetime.now(tz=timezone.utc)
            run.log_url = Template(settings.worker.log_url_template).render(
                run=run,
                correlation_id=correlation_id.get(),
            )
            session.commit()
            session.expunge_all()  # do not hold open DB connection while run is executed

        controller = TransferController(
            settings=settings,
            run=run,
            source_connection=source_connection,
            target_connection=target_connection,
            source_auth_data=source_auth_data,
            target_auth_data=target_auth_data,
        )
        controller.perform_transfer()
    except Exception as e:
        status = Status.FAILED
        logger.error("Run %r failed", run_id)
        exception = e
    else:
        status = Status.FINISHED
        logger.info("Run %r was successful", run_id)
        exception = None

    with Session(engine) as session:
        run = session.get(Run, run_id)
        if run:
            logger.info("Updating run %r status in DB", run_id)
            run.status = status
            run.ended_at = datetime.now(tz=timezone.utc)
            session.commit()

    if exception is not None:
        raise exception


@after_setup_task_logger.connect
def setup_loggers(*args, **kwargs):
    setup_logging(WorkerAppSettings().logging.get_log_config_path())
