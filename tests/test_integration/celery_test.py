from celery import Celery

from syncmaster.settings import Settings
from syncmaster.worker.base import WorkerTask

# TODO: remove settings object creating during import
settings = Settings()

celery = Celery(
    __name__,
    broker=settings.broker.url,
    backend="db+" + settings.database.sync_url,
    task_cls=WorkerTask,
    imports=[
        "syncmaster.worker.transfer",
        "tests.test_integration.test_scheduler.test_task",
    ],
)
