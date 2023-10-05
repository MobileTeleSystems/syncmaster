import os

from onetl.connection import Oracle, Postgres
from pyspark.sql import SparkSession

from app.config import EnvTypes, Settings


def get_worker_spark_session(settings: Settings) -> SparkSession:
    maven_packages = [
        p for connection in (Postgres, Oracle) for p in connection.get_packages()
    ]
    spark = (
        SparkSession.builder.appName("celery_worker")
        .config("spark.jars.packages", ",".join(maven_packages))
        .config("spark.sql.pyspark.jvmStacktrace.enabled", "true")
        .enableHiveSupport()
    )
    if settings.ENV == EnvTypes.GITLAB:
        spark = spark.config(
            "spark.jars.ivySettings", os.fspath(settings.IVYSETTINGS_PATH)
        )
    return spark.getOrCreate()
