# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
import logging
import os

from onetl.connection import Oracle, Postgres
from pyspark.sql import SparkSession

from app.config import EnvTypes, Settings
from app.dto.connections import (
    HiveConnectionDTO,
    OracleConnectionDTO,
    PostgresConnectionDTO,
)

log = logging.getLogger(__name__)


def get_worker_spark_session(
    settings: Settings,
    source: PostgresConnectionDTO | OracleConnectionDTO | HiveConnectionDTO,
    target: PostgresConnectionDTO | OracleConnectionDTO | HiveConnectionDTO,
) -> SparkSession:
    """Through the source and target parameters you can get credentials for authorization at the source"""

    maven_packages: list[str] = []
    for db_type in source, target:
        maven_packages.extend(get_packages(db_type=db_type.type))

    log.debug("Passing Maven packages: %s", maven_packages)
    spark = (
        SparkSession.builder.appName("celery_worker")
        .config("spark.jars.packages", ",".join(maven_packages))
        .config("spark.sql.pyspark.jvmStacktrace.enabled", "true")
    )
    if source.type == "hive" or target.type == "hive":
        log.debug("Enabling Hive support")
        spark = spark.enableHiveSupport()

    if settings.ENV == EnvTypes.GITLAB:
        log.debug("Passing custom ivysettings.xml")
        spark = spark.config("spark.jars.ivySettings", os.fspath(settings.IVYSETTINGS_PATH))
    return spark.getOrCreate()


def get_packages(db_type: str) -> list[str]:
    if db_type == "postgres":
        return Postgres.get_packages()
    if db_type == "oracle":
        return Oracle.get_packages()

    # If the database type does not require downloading .jar packages
    return []
