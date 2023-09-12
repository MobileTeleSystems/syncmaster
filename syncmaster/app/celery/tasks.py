from pyspark.sql import SparkSession
from sqlalchemy.orm import Session, selectinload

from app.celery.base import WorkerTask
from app.celery.config import celery
from app.celery.controller import TransferController
from app.db.models import Run, Status, Transfer
from app.exceptions.run import RunNotFoundException


@celery.task()
def run_transfer_task(self: WorkerTask, run_id: int) -> None:
    """Task for make transfer data"""
    with Session(self.engine) as session:
        run_transfer(session=session, run_id=run_id, spark=self.spark)


def run_transfer(session: Session, spark: SparkSession, run_id: int):
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
    else:
        run.status = Status.FINISHED
    session.add(run)
    session.commit()
