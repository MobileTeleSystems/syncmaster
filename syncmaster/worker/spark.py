# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from syncmaster.db.models import Run
from syncmaster.dto.connections import ConnectionDTO

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

log = logging.getLogger(__name__)


def get_worker_spark_session(
    run: Run,
    source: ConnectionDTO,
    target: ConnectionDTO,
) -> SparkSession:
    """Construct Spark Session using run parameters and application settings"""
    from pyspark.sql import SparkSession

    name = run.transfer.group.name + "_" + run.transfer.name  # noqa: WPS336
    spark_builder = SparkSession.builder.appName(f"syncmaster_{name}")

    for k, v in get_spark_session_conf(source, target, run.transfer.resources).items():
        spark_builder = spark_builder.config(k, v)

    if source.type == "hive" or target.type == "hive":  # type: ignore
        log.debug("Enabling Hive support")
        spark_builder = spark_builder.enableHiveSupport()

    return spark_builder.getOrCreate()


def get_packages(connection_type: str) -> list[str]:  # noqa: WPS212
    import pyspark
    from onetl.connection import MSSQL, Clickhouse, MySQL, Oracle, Postgres, SparkS3
    from onetl.file.format import XML, Excel

    # excel version is hardcoded due to https://github.com/nightscape/spark-excel/issues/902
    file_formats_spark_packages: list[str] = [
        *XML.get_packages(spark_version=pyspark.__version__),
        *Excel.get_packages(spark_version="3.5.1"),
    ]

    if connection_type == "postgres":
        return Postgres.get_packages()
    if connection_type == "oracle":
        return Oracle.get_packages()
    if connection_type == "clickhouse":
        return [
            "io.github.mtsongithub.doetl:spark-dialect-extension_2.12:0.0.2",
            *Clickhouse.get_packages(),
        ]
    if connection_type == "mssql":
        return MSSQL.get_packages()
    if connection_type == "mysql":
        return MySQL.get_packages()
    if connection_type == "s3":
        import pyspark

        spark_version = pyspark.__version__
        return SparkS3.get_packages(spark_version=spark_version) + file_formats_spark_packages

    if connection_type in ("hdfs", "sftp", "ftp", "ftps", "samba", "webdav"):
        return file_formats_spark_packages

    # If the database type does not require downloading .jar packages
    return []


def get_excluded_packages(db_type: str) -> list[str]:
    from onetl.connection import SparkS3

    return SparkS3.get_exclude_packages()


def get_spark_session_conf(
    source: ConnectionDTO,
    target: ConnectionDTO,
    resources: dict,
) -> dict:
    maven_packages: list[str] = []
    excluded_packages: list[str] = []

    for db_type in source, target:
        maven_packages.extend(get_packages(connection_type=db_type.type))  # type: ignore
        excluded_packages.extend(get_excluded_packages(db_type=db_type.type))  # type: ignore

    memory_mb = math.ceil(resources["ram_bytes_per_task"] / 1024 / 1024)
    config = {
        "spark.jars.packages": ",".join(maven_packages),
        "spark.sql.pyspark.jvmStacktrace.enabled": "true",
        "spark.hadoop.mapreduce.fileoutputcommitter.marksuccessfuljobs": "false",
        "spark.executor.cores": resources["cpu_cores_per_task"],
        # Spark expects memory to be in MB
        "spark.executor.memory": f"{memory_mb}M",
        "spark.executor.instances": resources["max_parallel_tasks"],
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
