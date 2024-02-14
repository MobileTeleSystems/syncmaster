from onetl.connection import SparkHDFS
from onetl.hooks import hook

from app.tasks.utils import get_worker_spark_session  # noqa: F401


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
