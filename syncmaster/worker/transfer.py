# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import logging
from datetime import datetime, timezone

import onetl
from asgi_correlation_id import correlation_id
from celery.signals import after_setup_logger, before_task_publish, task_prerun
from celery.utils.log import get_task_logger
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from syncmaster.backend.middlewares.logging import setup_logging
from syncmaster.backend.settings import BackendSettings as Settings
from syncmaster.db.models import AuthData, Run, Status, Transfer
from syncmaster.db.repositories.utils import decrypt_auth_data
from syncmaster.exceptions.run import RunNotFoundError
from syncmaster.worker.base import WorkerTask
from syncmaster.worker.config import celery
from syncmaster.worker.controller import TransferController
from syncmaster.worker.settings import get_worker_settings

logger = get_task_logger(__name__)

CORRELATION_CELERY_HEADER_ID = get_worker_settings().CORRELATION_CELERY_HEADER_ID


@celery.task(name="run_transfer_task", bind=True, track_started=True)
def run_transfer_task(self: WorkerTask, run_id: int) -> None:
    onetl.log.setup_logging(level=logging.INFO)
    with Session(self.engine) as session:
        run_transfer(
            session=session,
            run_id=run_id,
            settings=self.settings,
        )


def run_transfer(session: Session, run_id: int, settings: Settings):
    logger.info("Start transfer")
    run = session.get(
        Run,
        run_id,
        options=(
            selectinload(Run.transfer),
            selectinload(Run.transfer).selectinload(Transfer.group),
            selectinload(Run.transfer).selectinload(Transfer.source_connection),
            selectinload(Run.transfer).selectinload(Transfer.target_connection),
        ),
    )
    if run is None:
        raise RunNotFoundError

    run.status = Status.STARTED
    run.started_at = datetime.now(tz=timezone.utc)
    session.add(run)
    session.commit()

    q_source_auth_data = select(AuthData).where(AuthData.connection_id == run.transfer.source_connection.id)
    q_target_auth_data = select(AuthData).where(AuthData.connection_id == run.transfer.target_connection.id)

    target_auth_data = decrypt_auth_data(session.scalars(q_target_auth_data).one().value, settings)
    source_auth_data = decrypt_auth_data(session.scalars(q_source_auth_data).one().value, settings)

    try:
        controller = TransferController(
            run=run,
            source_connection=run.transfer.source_connection,
            target_connection=run.transfer.target_connection,
            source_auth_data=source_auth_data,
            target_auth_data=target_auth_data,
        )
        controller.perform_transfer()
    except Exception:
        run.status = Status.FAILED
        logger.exception("Run %r was failed", run.id)
    else:
        run.status = Status.FINISHED
        logger.warning("Run %r was successful", run.id)

    run.ended_at = datetime.now(tz=timezone.utc)
    session.add(run)
    session.commit()


@after_setup_logger.connect
def setup_loggers(*args, **kwargs):
    setup_logging(Settings().logging.get_log_config_path())


@before_task_publish.connect()
def transfer_correlation_id(headers, *args, **kwargs) -> None:
    # This is called before task.delay() finishes
    # Here we're able to transfer the correlation ID via the headers kept in our backend
    headers[CORRELATION_CELERY_HEADER_ID] = correlation_id.get()


@task_prerun.connect()
def load_correlation_id(task, *args, **kwargs) -> None:
    # This is called when the worker picks up the task
    # Here we're able to load the correlation ID from the headers
    id_value = task.request.get(CORRELATION_CELERY_HEADER_ID)
    correlation_id.set(id_value)
