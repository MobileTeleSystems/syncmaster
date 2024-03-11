from __future__ import annotations

import logging
import os
from pathlib import Path

from celery.signals import worker_process_init, worker_process_shutdown
from coverage import Coverage
from onetl.connection import SparkHDFS
from onetl.hooks import hook
from pyspark.sql import SparkSession

from app.config import EnvTypes, Settings
from app.dto.connections import ConnectionDTO
from app.tasks.utils import get_spark_session_conf

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


def get_ivy_settings_conf(settings: Settings) -> dict:
    config = {}
    if settings.ENV == EnvTypes.GITLAB:
        log.debug("Passing custom ivysettings.xml")
        config.update(
            {
                "spark.jars.ivySettings": os.fspath(
                    Path(__file__).parent.parent.parent / "tests" / "config" / "ivysettings.xml"
                ),
            }
        )
    return config


def get_worker_spark_session(
    settings: Settings,
    source: ConnectionDTO,
    target: ConnectionDTO,
) -> SparkSession:
    ivy_settings_conf = get_ivy_settings_conf(settings)

    spark_builder = SparkSession.builder.appName("celery_worker")

    for k, v in get_spark_session_conf(source, target).items():
        spark_builder = spark_builder.config(k, v)

    if source.type == "hive" or target.type == "hive":  # type: ignore
        log.debug("Enabling Hive support")
        spark_builder = spark_builder.enableHiveSupport()

    if ivy_settings_conf:
        for k, v in ivy_settings_conf.items():
            spark_builder = spark_builder.config(k, v)

    return spark_builder.getOrCreate()


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
