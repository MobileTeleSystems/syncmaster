# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from datetime import datetime, timezone

from asgi_correlation_id import correlation_id
from asgi_correlation_id.extensions.celery import load_correlation_ids
from celery import Celery
from celery.signals import after_setup_task_logger
from celery.utils.log import get_task_logger
from jinja2 import Template
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from syncmaster.db.models import AuthData, Run, Status, Transfer
from syncmaster.db.repositories.utils import decrypt_auth_data
from syncmaster.exceptions.run import RunNotFoundError
from syncmaster.settings.log import setup_logging
from syncmaster.worker.celery import app as celery
from syncmaster.worker.controller import TransferController
from syncmaster.worker.settings import WorkerAppSettings

logger = get_task_logger(__name__)
load_correlation_ids()


@celery.task(name="run_transfer_task", bind=True, track_started=True)
def run_transfer_task(self: Celery, run_id: int) -> None:
    with Session(self.engine) as session:
        run_transfer(
            session=session,
            run_id=run_id,
            settings=self.settings,
        )


def run_transfer(session: Session, run_id: int, settings: WorkerAppSettings):
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
    run.log_url = Template(settings.worker.log_url_template).render(run=run, correlation_id=correlation_id.get())
    session.add(run)
    session.commit()

    q_source_auth_data = select(AuthData).where(AuthData.connection_id == run.transfer.source_connection.id)
    q_target_auth_data = select(AuthData).where(AuthData.connection_id == run.transfer.target_connection.id)

    source_auth_result = session.scalars(q_source_auth_data).one_or_none()
    target_auth_result = session.scalars(q_target_auth_data).one_or_none()
    source_auth_data = decrypt_auth_data(source_auth_result.value, settings) if source_auth_result else None
    target_auth_data = decrypt_auth_data(target_auth_result.value, settings) if target_auth_result else None

    try:
        controller = TransferController(
            settings=settings,
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


@after_setup_task_logger.connect
def setup_loggers(*args, **kwargs):
    setup_logging(WorkerAppSettings().logging.get_log_config_path())
