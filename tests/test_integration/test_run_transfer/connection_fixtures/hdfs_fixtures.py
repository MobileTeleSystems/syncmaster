import logging
import os
import secrets
from collections import namedtuple
from pathlib import PurePosixPath

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Group
from syncmaster.dto.connections import HDFSConnectionDTO
from tests.settings import TestSettings
from tests.test_unit.utils import create_connection, upload_files

logger = logging.getLogger(__name__)


@pytest.fixture(
    scope="session",
    params=[pytest.param("hdfs", marks=[pytest.mark.hdfs])],
)
def hdfs(test_settings: TestSettings) -> HDFSConnectionDTO:
    return HDFSConnectionDTO(
        cluster=test_settings.TEST_HIVE_CLUSTER,
    )


@pytest.fixture(scope="session")
def hdfs_server():
    HDFSServer = namedtuple("HDFSServer", ["host", "webhdfs_port", "ipc_port"])
    return HDFSServer(
        host=os.getenv("TEST_HDFS_HOST"),
        webhdfs_port=os.getenv("TEST_HDFS_WEBHDFS_PORT"),
        ipc_port=os.getenv("TEST_HDFS_IPC_PORT"),
    )


@pytest.fixture(scope="session")
def hdfs_file_df_connection(spark, hdfs_server):
    from onetl.connection import SparkHDFS

    return SparkHDFS(
        cluster="test-hive",
        host=hdfs_server.host,
        ipc_port=hdfs_server.ipc_port,
        spark=spark,
    )


@pytest.fixture(scope="session")
def hdfs_file_connection(hdfs_server):
    from onetl.connection import HDFS

    return HDFS(cluster="test-hive", host=hdfs_server.host, webhdfs_port=hdfs_server.webhdfs_port)


@pytest.fixture()
def hdfs_file_connection_with_path(request, hdfs_file_connection):
    connection = hdfs_file_connection
    source = PurePosixPath("/data")
    target = PurePosixPath("/target")

    def finalizer():
        connection.remove_dir(source, recursive=True)
        connection.remove_dir(target, recursive=True)

    request.addfinalizer(finalizer)

    connection.remove_dir(source, recursive=True)
    connection.remove_dir(target, recursive=True)
    connection.create_dir(source)

    return connection, source


@pytest.fixture()
def hdfs_file_df_connection_with_path(hdfs_file_connection_with_path, hdfs_file_df_connection):
    _, source = hdfs_file_connection_with_path
    return hdfs_file_df_connection, source


@pytest.fixture()
def prepare_hdfs(
    hdfs_file_df_connection_with_path,
    hdfs_file_connection,
    resource_path,
):
    logger.info("START PREPARE HDFS")
    connection, upload_to = hdfs_file_df_connection_with_path
    files = upload_files(resource_path, upload_to, hdfs_file_connection)
    logger.info("END PREPARE HDFS")
    return connection, upload_to, files


@pytest_asyncio.fixture
async def hdfs_connection(
    hdfs: HDFSConnectionDTO,
    session: AsyncSession,
    group: Group,
):
    result = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        type=hdfs.type,
        data=dict(
            cluster=hdfs.cluster,
        ),
        group_id=group.id,
    )

    # no credentials for test purpose

    yield result
    await session.delete(result)
    await session.commit()
