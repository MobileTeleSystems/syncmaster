from __future__ import annotations

from celery.signals import worker_process_init, worker_process_shutdown
from coverage import Coverage
from onetl.connection import SparkHDFS
from onetl.hooks import hook

from syncmaster.worker.spark import get_worker_spark_session

# this is just to automatically import hooks
get_worker_spark_session = get_worker_spark_session


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
