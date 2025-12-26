from __future__ import annotations

from celery.signals import worker_process_init, worker_process_shutdown
from coverage import Coverage
from onetl.connection import HDFS, SparkHDFS
from onetl.hooks import hook

# this is just to automatically import hooks
from syncmaster.worker.spark import get_worker_spark_session  # noqa: F401


@SparkHDFS.Slots.get_cluster_namenodes.bind
@HDFS.Slots.get_cluster_namenodes.bind
@hook
def get_cluster_namenodes(cluster: str) -> set[str] | None:
    if cluster == "test-hive":
        return {"test-hive"}
    return None


@HDFS.Slots.is_namenode_active.bind
@SparkHDFS.Slots.is_namenode_active.bind
@hook
def is_namenode_active(host: str, cluster: str) -> bool:
    return cluster == "test-hive"


@SparkHDFS.Slots.get_ipc_port.bind
@hook
def get_ipc_port(cluster: str) -> int | None:
    if cluster == "test-hive":
        return 9820
    return None


@HDFS.Slots.get_webhdfs_port.bind
@hook
def get_webhdfs_port(cluster: str) -> int | None:
    if cluster == "test-hive":
        return 9870
    return None


# Needed to collect code coverage by tests in the worker
# https://github.com/nedbat/coveragepy/issues/689#issuecomment-656706935
COV = None


@worker_process_init.connect
def start_coverage(**kwargs):
    global COV  # noqa: PLW0603

    COV = Coverage(data_suffix=True)
    COV.start()


@worker_process_shutdown.connect
def save_coverage(**kwargs):
    if COV is not None:
        COV.stop()
        COV.save()
