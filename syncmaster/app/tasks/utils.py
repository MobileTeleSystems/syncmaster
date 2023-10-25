import os

from onetl.connection import Oracle, Postgres
from pyspark.sql import SparkSession

from app.config import EnvTypes, Settings
from app.dto.connections import (
    HiveConnectionDTO,
    OracleConnectionDTO,
    PostgresConnectionDTO,
)


def get_worker_spark_session(
    settings: Settings,
    source: PostgresConnectionDTO | OracleConnectionDTO | HiveConnectionDTO,
    target: PostgresConnectionDTO | OracleConnectionDTO | HiveConnectionDTO,
) -> SparkSession:
    """Through the source and target parameters you can get credentials for authorization at the source"""

    maven_packages = [
        *Postgres.get_packages(),
        *Oracle.get_packages(),
    ]

    spark = (
        SparkSession.builder.appName("celery_worker")
        .config("spark.jars.packages", ",".join(maven_packages))
        .config("spark.sql.pyspark.jvmStacktrace.enabled", "true")
    )
    if source.type == "hive" or target.type == "hive":
        spark = spark.enableHiveSupport()

    if settings.ENV == EnvTypes.GITLAB:
        spark = spark.config(
            "spark.jars.ivySettings", os.fspath(settings.IVYSETTINGS_PATH)
        )
    return spark.getOrCreate()
