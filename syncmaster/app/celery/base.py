from celery import Task
from onetl.connection import Oracle, Postgres
from pyspark.sql import SparkSession
from sqlalchemy import create_engine

from app.config import Settings


class WorkerTask(Task):
    def __init__(self) -> None:
        self.settings = Settings()
        maven_packages = [
            p for connection in (Postgres, Oracle) for p in connection.get_packages()
        ]
        self.spark: SparkSession = (
            SparkSession.builder.appName("celery_worker")
            .config("spark.jars.apckaes", ",".join(maven_packages))
            .getOrCreate()
        )
        self.engine = create_engine(
            url=self.settings.build_db_connection_uri(driver="psycopg2")
        )
