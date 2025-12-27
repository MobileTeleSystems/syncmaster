#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from syncmaster.worker.ivy2 import get_excluded_packages, get_packages

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

log = logging.getLogger(__name__)


def get_spark_session_conf_for_docker_image(connection_types: set[str]) -> dict:
    maven_packages: list[str] = get_packages(connection_types=connection_types or {"all"})
    excluded_packages: list[str] = get_excluded_packages()

    return {
        "spark.jars.packages": ",".join(maven_packages),
        "spark.jars.excludes": ",".join(excluded_packages),
        "spark.sql.pyspark.jvmStacktrace.enabled": "true",
        # use only minimal available resources
        "spark.driver.cores": "1",
        "spark.driver.memory": "512M",
        "spark.executor.cores": "1",
        "spark.executor.memory": "512M",
        "spark.executor.instances": "1",
        "spark.ui.enabled": "false",
    }


def get_worker_spark_session_for_docker(connection_types: set[str]) -> SparkSession:
    """
    Construct dummy Spark session with all .jars included.
    Designed to be used in Dockerfile.worker to populate the image.
    """
    from pyspark.sql import SparkSession  # noqa: PLC0415

    spark_builder = SparkSession.builder.appName("syncmaster_jar_downloader").master("local[1]")

    for k, v in get_spark_session_conf_for_docker_image(connection_types).items():
        spark_builder = spark_builder.config(k, v)

    return spark_builder.getOrCreate()


def download_maven_packages(connection_types: set[str]):
    log.info("Downloading Maven packages for connectors %s...", connection_types)
    with get_worker_spark_session_for_docker(connection_types):
        log.info("Done!")


if __name__ == "__main__":
    connection_types = "all"
    if len(sys.argv) > 1:
        connection_types = sys.argv[1:]
    download_maven_packages(set(connection_types))
