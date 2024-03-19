# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
import logging
from datetime import datetime

import onetl
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from syncmaster.config import Settings
from syncmaster.db.models import AuthData, Run, Status, Transfer
from syncmaster.db.repositories.utils import decrypt_auth_data
from syncmaster.exceptions.run import RunNotFoundError
from syncmaster.worker.base import WorkerTask
from syncmaster.worker.config import celery
from syncmaster.worker.controller import TransferController

logger = logging.getLogger(__name__)


@celery.task(name="run_transfer_task", bind=True, track_started=True)
def run_transfer_task(self: WorkerTask, run_id: int) -> None:
    onetl.log.setup_logging(level=logging.INFO)
    """Task for make transfer data"""
    logger.info("Before spark initializing")
    logger.info("Spark initialized")
    with Session(self.engine) as session:
        run_transfer(
            session=session,
            run_id=run_id,
            settings=self.settings,
        )


def run_transfer(session: Session, run_id: int, settings: Settings):
    logger.info("Start transfering")
    run = session.get(
        Run,
        run_id,
        options=(
            selectinload(Run.transfer).selectinload(Transfer.source_connection),
            selectinload(Run.transfer).selectinload(Transfer.target_connection),
        ),
    )
    if run is None:
        raise RunNotFoundError
    run.status = Status.STARTED
    run.started_at = datetime.utcnow()
    session.add(run)
    session.commit()

    controller = None

    q_source_auth_data = select(AuthData).where(AuthData.connection_id == run.transfer.source_connection.id)
    q_target_auth_data = select(AuthData).where(AuthData.connection_id == run.transfer.target_connection.id)

    target_auth_data = decrypt_auth_data(session.scalars(q_target_auth_data).one().value, settings)
    source_auth_data = decrypt_auth_data(session.scalars(q_source_auth_data).one().value, settings)

    try:
        controller = TransferController(
            transfer=run.transfer,
            source_connection=run.transfer.source_connection,
            target_connection=run.transfer.target_connection,
            source_auth_data=source_auth_data,
            target_auth_data=target_auth_data,
            settings=settings,
        )
        controller.start_transfer()
    except Exception:
        run.status = Status.FAILED
        logger.exception("Run `%s` was failed", run.id)
    else:
        run.status = Status.FINISHED
        logger.warning("Run `%s` was successful", run.id)
    finally:
        # Both the source and the receiver use the same spark session,
        # so it is enough to stop the session at the source.
        if controller is not None and controller.source_handler.spark is not None:
            controller.source_handler.spark.sparkContext.stop()
            controller.source_handler.spark.stop()

    run.ended_at = datetime.utcnow()
    session.add(run)
    session.commit()
