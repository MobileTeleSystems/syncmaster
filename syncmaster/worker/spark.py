# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from syncmaster.config import Settings
from syncmaster.db.models import Run
from syncmaster.dto.connections import ConnectionDTO

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

log = logging.getLogger(__name__)


def get_worker_spark_session(
    settings: Settings,
    run: Run,
    source: ConnectionDTO,
    target: ConnectionDTO,
) -> SparkSession:
    """Construct Spark Session using run parameters and application settings"""
    from pyspark.sql import SparkSession

    name = run.transfer.group.name + "_" + run.transfer.name
    spark_builder = SparkSession.builder.appName(f"syncmaster_{name}")

    for k, v in get_spark_session_conf(source, target).items():
        spark_builder = spark_builder.config(k, v)

    if source.type == "hive" or target.type == "hive":  # type: ignore
        log.debug("Enabling Hive support")
        spark_builder = spark_builder.enableHiveSupport()

    return spark_builder.getOrCreate()


def get_packages(db_type: str) -> list[str]:
    from onetl.connection import Oracle, Postgres, SparkS3

    if db_type == "postgres":
        return Postgres.get_packages()
    if db_type == "oracle":
        return Oracle.get_packages()
    if db_type == "s3":
        import pyspark

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


def get_spark_session_conf(
    source: ConnectionDTO,
    target: ConnectionDTO,
) -> dict:
    maven_packages: list[str] = []
    excluded_packages: list[str] = []

    for db_type in source, target:
        maven_packages.extend(get_packages(db_type=db_type.type))  # type: ignore
        excluded_packages.extend(get_excluded_packages(db_type=db_type.type))  # type: ignore

    config = {
        "spark.jars.packages": ",".join(maven_packages),
        "spark.sql.pyspark.jvmStacktrace.enabled": "true",
    }

    if maven_packages:
        log.debug("Include Maven packages: %s", maven_packages)
        config["spark.jars.packages"] = ",".join(maven_packages)

    if excluded_packages:
        log.debug("Exclude Maven packages: %s", excluded_packages)
        config["spark.jars.excludes"] = ",".join(excluded_packages)

    if target.type == "s3":  # type: ignore
        config.update(
            {
                "spark.hadoop.fs.s3a.committer.magic.enabled": "true",
                "spark.hadoop.fs.s3a.committer.name": "magic",
                "spark.hadoop.mapreduce.outputcommitter.factory.scheme.s3a": (
                    "org.apache.hadoop.fs.s3a.commit.S3ACommitterFactory"
                ),
                "spark.sql.parquet.output.committer.class": (
                    "org.apache.spark.internal.io.cloud.BindingParquetOutputCommitter"
                ),
                "spark.sql.sources.commitProtocolClass": "org.apache.spark.internal.io.cloud.PathOutputCommitProtocol",
            },
        )

    return config
