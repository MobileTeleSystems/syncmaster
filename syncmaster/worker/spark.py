# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import logging
import math
import socket
from typing import TYPE_CHECKING

from onetl.connection.kerberos_helpers import kinit_password

from syncmaster.dto.connections import (
    ConnectionDTO,
    HDFSConnectionDTO,
    HiveConnectionDTO,
)
from syncmaster.worker.ivy2 import get_excluded_packages, get_packages

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

    from syncmaster.db.models import Run
    from syncmaster.worker.settings import WorkerSettings

log = logging.getLogger(__name__)


def get_worker_spark_session(
    run: Run,
    source: ConnectionDTO,
    target: ConnectionDTO,
    settings: WorkerSettings,
) -> SparkSession:
    """Construct Spark Session using run parameters and application settings"""
    from pyspark.sql import SparkSession  # noqa: PLC0415

    name = run.transfer.group.name + "_" + run.transfer.name
    spark_builder = SparkSession.builder.appName(f"SyncMaster__{name}")

    master = settings.spark_session_default_config.get("spark.master")
    spark_session_config = settings.spark_session_default_config.copy()
    spark_session_config.update(get_spark_session_conf(master, source, target, run.transfer.resources))

    for k, v in spark_session_config.items():
        spark_builder = spark_builder.config(k, v)

    for entity in source, target:
        if isinstance(entity, HiveConnectionDTO):
            log.debug("Enabling Hive support")
            spark_builder = spark_builder.enableHiveSupport()

        if isinstance(entity, (HiveConnectionDTO, HDFSConnectionDTO)):
            log.debug("Using Kerberos auth for %s", entity.user)
            kinit_password(entity.user, entity.password)

    return spark_builder.getOrCreate()


def get_spark_session_conf(
    spark_master: str | None,
    source: ConnectionDTO,
    target: ConnectionDTO,
    resources: dict,
) -> dict:
    maven_packages: list[str] = get_packages(connection_types={source.type, target.type})
    excluded_packages: list[str] = get_excluded_packages()

    tasks: int = resources["max_parallel_tasks"]
    cores_per_task: int = resources["cpu_cores_per_task"]
    # Spark expects memory to be in MB
    memory_mb: int = math.ceil(resources["ram_bytes_per_task"] / 1024 / 1024)

    config: dict[str, str | int] = {
        "spark.sql.pyspark.jvmStacktrace.enabled": "true",
        "spark.hadoop.mapreduce.fileoutputcommitter.marksuccessfuljobs": "false",
    }

    if spark_master and spark_master.startswith("local"):
        config["spark.master"] = f"local[{tasks}]"
        config["spark.driver.memory"] = f"{memory_mb}M"
    else:
        config["spark.executor.memory"] = f"{memory_mb}M"
        config["spark.executor.instances"] = tasks

    config["spark.executor.cores"] = cores_per_task
    config["spark.default.parallelism"] = tasks * cores_per_task
    config["spark.dynamicAllocation.maxExecutors"] = tasks  # yarn
    config["spark.kubernetes.executor.limit.cores"] = cores_per_task  # k8s

    # https://spark.apache.org/docs/latest/running-on-kubernetes.html#client-mode-executor-pod-garbage-collection
    config["spark.kubernetes.driver.pod.name"] = socket.gethostname()

    if maven_packages:
        log.debug("Include Maven packages: %s", maven_packages)
        config["spark.jars.packages"] = ",".join(maven_packages)

    if excluded_packages:
        log.debug("Exclude Maven packages: %s", excluded_packages)
        config["spark.jars.excludes"] = ",".join(excluded_packages)

    if target.type == "s3":
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
