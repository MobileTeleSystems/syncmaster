from __future__ import annotations

import logging

from celery.signals import worker_process_init, worker_process_shutdown
from coverage import Coverage
from onetl.connection import SparkHDFS
from onetl.hooks import hook
from pyspark.sql import SparkSession

from syncmaster.config import Settings
from syncmaster.dto.connections import ConnectionDTO
from syncmaster.worker.spark import get_spark_session_conf

log = logging.getLogger(__name__)


@SparkHDFS.Slots.get_cluster_namenodes.bind
@hook
def get_cluster_namenodes(cluster: str) -> set[str] | None:
    if cluster == "test-hive":
        return {"test-hive"}
    return None


@SparkHDFS.Slots.is_namenode_active.bind
@hook
def is_namenode_active(host: str, cluster: str) -> bool:
    if cluster == "test-hive":
        return True
    return False


@SparkHDFS.Slots.get_ipc_port.bind
@hook
def get_ipc_port(cluster: str) -> int | None:
    if cluster == "test-hive":
        return 9820
    return None


def get_worker_spark_session(
    settings: Settings,
    source: ConnectionDTO,
    target: ConnectionDTO,
) -> SparkSession:
    spark_builder = SparkSession.builder.appName("celery_worker")

    for k, v in get_spark_session_conf(source, target).items():
        spark_builder = spark_builder.config(k, v)

    if source.type == "hive" or target.type == "hive":
        log.debug("Enabling Hive support")
        spark_builder = spark_builder.enableHiveSupport()

    return spark_builder.getOrCreate()


# Needed to collect code coverage by tests in the worker
# https://github.com/nedbat/coveragepy/issues/689#issuecomment-656706935


COV = None


@worker_process_init.connect
def start_coverage(**kwargs):
    global COV

    COV = Coverage(data_suffix=True)
    COV.start()


@worker_process_shutdown.connect
def save_coverage(**kwargs):
    if COV is not None:
        COV.stop()
        COV.save()
