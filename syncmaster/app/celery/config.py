from celery import Celery

from app.celery.base import WorkerTask
from app.config import Settings

settings = Settings()

celery = Celery(
    __name__,
    broker=settings.build_rabbit_connection_uri(),
    backend="db+" + settings.build_db_connection_uri(driver="psycopg2"),
    task_cls=WorkerTask,
)
