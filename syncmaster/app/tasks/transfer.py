import logging
from datetime import datetime

import onetl
from pyspark.sql import SparkSession
from sqlalchemy.orm import Session, selectinload

from app.db.models import Run, Status, Transfer
from app.exceptions.run import RunNotFoundException
from app.tasks.base import WorkerTask
from app.tasks.config import celery
from app.tasks.controller import TransferController

logger = logging.getLogger(__name__)


@celery.task(name="run_transfer_task", bind=True, track_started=True)
def run_transfer_task(self: WorkerTask, run_id: int) -> None:
    onetl.log.setup_logging(level=logging.INFO)
    """Task for make transfer data"""
    logger.info("Before spark initializing")
    spark = self.settings.CREATE_SPARK_SESSION_FUNCTION(self.settings)
    logger.info("Spark initialized")
    with Session(self.engine) as session:
        run_transfer(session=session, run_id=run_id, spark=spark)


def run_transfer(session: Session, spark: SparkSession, run_id: int):
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
        raise RunNotFoundException
    run.status = Status.STARTED
    run.started_at = datetime.utcnow()
    session.add(run)
    session.commit()

    try:
        controller = TransferController(
            transfer=run.transfer,
            source_connection=run.transfer.source_connection,
            target_connection=run.transfer.target_connection,
            spark=spark,
        )
        controller.make_transfer()
    except Exception:
        run.status = Status.FAILED
        logger.exception("Run `%s` was failed", run.id)
    else:
        run.status = Status.FINISHED
        logger.warning("Run `%s` was successful", run.id)
    run.ended_at = datetime.utcnow()
    session.add(run)
    session.commit()
