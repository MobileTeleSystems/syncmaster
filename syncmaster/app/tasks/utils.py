# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
import logging
import os

import pyspark
from onetl.connection import Oracle, Postgres, SparkS3
from pyspark.sql import SparkSession

from app.config import EnvTypes, Settings
from app.dto.connections import ConnectionDTO

log = logging.getLogger(__name__)


def get_worker_spark_session(
    settings: Settings,
    source: ConnectionDTO,
    target: ConnectionDTO,
) -> SparkSession:
    """Through the source and target parameters you can get credentials for authorization at the source"""

    maven_packages: list[str] = []
    excluded_packages: list[str] = []

    for db_type in source, target:
        maven_packages.extend(get_packages(db_type=db_type.type))  # type: ignore
        excluded_packages.extend(get_excluded_packages(db_type=db_type.type))  # type: ignore

    log.debug("Passing Maven packages: %s", maven_packages)
    spark = (
        SparkSession.builder.appName("celery_worker")
        .config("spark.jars.packages", ",".join(maven_packages))
        .config("spark.sql.pyspark.jvmStacktrace.enabled", "true")
    )

    if source.type == "s3":  # type: ignore
        spark = (
            spark.config("spark.jars.excludes", ",".join(excluded_packages))
            .config("spark.hadoop.fs.s3a.committer.magic.enabled", "true")
            .config("spark.hadoop.fs.s3a.committer.name", "magic")
            .config(
                "spark.hadoop.mapreduce.outputcommitter.factory.scheme.s3a",
                "org.apache.hadoop.fs.s3a.commit.S3ACommitterFactory",
            )
            .config(
                "spark.sql.parquet.output.committer.class",
                "org.apache.spark.internal.io.cloud.BindingParquetOutputCommitter",
            )
            .config(
                "spark.sql.sources.commitProtocolClass",
                "org.apache.spark.internal.io.cloud.PathOutputCommitProtocol",
            )
        )

    if source.type == "hive" or target.type == "hive":  # type: ignore
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
    if db_type == "s3":
        spark_version = pyspark.__version__
        return SparkS3.get_packages(spark_version=spark_version)

    # If the database type does not require downloading .jar packages
    return []


def get_excluded_packages(db_type: str):
    if db_type == "s3":
        return [
            "com.google.cloud.bigdataoss:gcs-connector",
            "org.apache.hadoop:hadoop-aliyun",
            "org.apache.hadoop:hadoop-azure-datalake",
            "org.apache.hadoop:hadoop-azure",
        ]
    return []
