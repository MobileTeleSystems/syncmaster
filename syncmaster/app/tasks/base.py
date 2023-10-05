from celery import Task
from sqlalchemy import create_engine

from app.config import Settings


class WorkerTask(Task):
    def __init__(self) -> None:
        self.settings = Settings()
        self.engine = create_engine(
            url=self.settings.build_db_connection_uri(driver="psycopg2"),
        )
