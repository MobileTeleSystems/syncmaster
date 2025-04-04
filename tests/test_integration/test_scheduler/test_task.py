import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from syncmaster.db.models.run import Run, Status
from syncmaster.exceptions.run import RunNotFoundError
from syncmaster.scheduler.celery import app as celery
from syncmaster.worker.base import WorkerTask


@celery.task(name="tick", bind=True, track_started=True)
def tick(self: WorkerTask, run_id: int) -> None:
    with Session(self.engine) as session:
        run = session.get(Run, run_id)
        if run is None:
            raise RunNotFoundError

        run.started_at = datetime.now(tz=timezone.utc)
        run.status = Status.STARTED
        session.add(run)
        session.commit()

        time.sleep(2)  # to make sure that previous status is handled in test
        run.status = Status.FINISHED
        run.ended_at = datetime.now(tz=timezone.utc)
        session.add(run)
        session.commit()
