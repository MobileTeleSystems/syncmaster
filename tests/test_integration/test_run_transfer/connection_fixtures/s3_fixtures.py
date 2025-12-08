import logging
import secrets
from collections import namedtuple
from pathlib import PosixPath, PurePosixPath

import pytest
import pytest_asyncio
from onetl.connection import S3, SparkS3
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Group
from syncmaster.dto.connections import S3ConnectionDTO
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.settings import TestSettings
from tests.test_unit.utils import create_connection, create_credentials, upload_files

logger = logging.getLogger(__name__)


@pytest.fixture(
    scope="session",
    params=[pytest.param("s3", marks=[pytest.mark.s3])],
)
def s3_for_conftest(test_settings: TestSettings) -> S3ConnectionDTO:
    return S3ConnectionDTO(
        host=test_settings.TEST_S3_HOST_FOR_CONFTEST,
        port=test_settings.TEST_S3_PORT_FOR_CONFTEST,
        bucket=test_settings.TEST_S3_BUCKET,
        bucket_style=test_settings.TEST_S3_BUCKET_STYLE,
        region=test_settings.TEST_S3_REGION,
        access_key=test_settings.TEST_S3_ACCESS_KEY,
        secret_key=test_settings.TEST_S3_SECRET_KEY,
        protocol=test_settings.TEST_S3_PROTOCOL,
        additional_params=test_settings.TEST_S3_ADDITIONAL_PARAMS,
    )


@pytest.fixture(
    scope="session",
    params=[pytest.param("s3", marks=[pytest.mark.s3])],
)
def s3_for_worker(test_settings: TestSettings) -> S3ConnectionDTO:
    return S3ConnectionDTO(
        host=test_settings.TEST_S3_HOST_FOR_WORKER,
        port=test_settings.TEST_S3_PORT_FOR_WORKER,
        bucket=test_settings.TEST_S3_BUCKET,
        bucket_style=test_settings.TEST_S3_BUCKET_STYLE,
        region=test_settings.TEST_S3_REGION,
        access_key=test_settings.TEST_S3_ACCESS_KEY,
        secret_key=test_settings.TEST_S3_SECRET_KEY,
        protocol=test_settings.TEST_S3_PROTOCOL,
        additional_params=test_settings.TEST_S3_ADDITIONAL_PARAMS,
    )


@pytest.fixture(scope="session")
def s3_server(s3_for_conftest):
    S3Server = namedtuple(
        "S3Server",
        ["host", "port", "bucket", "bucket_style", "region", "access_key", "secret_key", "protocol"],
    )

    return S3Server(
        host=s3_for_conftest.host,
        port=s3_for_conftest.port,
        bucket=s3_for_conftest.bucket,
        bucket_style=s3_for_conftest.bucket_style,
        region=s3_for_conftest.region,
        access_key=s3_for_conftest.access_key,
        secret_key=s3_for_conftest.secret_key,
        protocol=s3_for_conftest.protocol,
    )


@pytest.fixture(scope="session")
def s3_file_connection(s3_server):
    from onetl.connection import S3

    s3_connection = S3(
        host=s3_server.host,
        port=s3_server.port,
        bucket=s3_server.bucket,
        region=s3_server.region,
        access_key=s3_server.access_key,
        secret_key=s3_server.secret_key,
        protocol=s3_server.protocol,
    )

    if not s3_connection.client.bucket_exists(s3_server.bucket):
        s3_connection.client.make_bucket(s3_server.bucket)

    return s3_connection


@pytest.fixture
def s3_file_connection_with_path(request, s3_file_connection):
    connection = s3_file_connection
    source = PurePosixPath("/data")
    target = PurePosixPath("/target")

    def finalizer():
        connection.remove_dir(source, recursive=True)
        connection.remove_dir(target, recursive=True)

    request.addfinalizer(finalizer)
    connection.remove_dir(source, recursive=True)
    connection.remove_dir(target, recursive=True)

    return connection, source


@pytest.fixture
def s3_file_df_connection_with_path(s3_file_connection_with_path, s3_file_df_connection):
    _, root = s3_file_connection_with_path
    return s3_file_df_connection, root


@pytest.fixture(scope="session")
def s3_file_df_connection(s3_file_connection, spark, s3_server):
    from onetl.connection import SparkS3

    return SparkS3(
        host=s3_server.host,
        port=s3_server.port,
        bucket=s3_server.bucket,
        protocol=s3_server.protocol,
        path_style_access=s3_server.bucket_style == "path",
        region=s3_server.region,
        access_key=s3_server.access_key,
        secret_key=s3_server.secret_key,
        spark=spark,
    )


@pytest.fixture
def prepare_s3(
    resource_path: PosixPath,
    s3_file_connection: S3,
    s3_file_df_connection_with_path: tuple[SparkS3, PurePosixPath],
):
    logger.info("START PREPARE S3")
    connection, remote_path = s3_file_df_connection_with_path

    s3_file_connection.remove_dir(remote_path, recursive=True)
    files = upload_files(resource_path, remote_path, s3_file_connection)

    yield connection, remote_path, files

    logger.info("START POST-CLEANUP S3")
    s3_file_connection.remove_dir(remote_path, recursive=True)
    logger.info("END POST-CLEANUP S3")


@pytest_asyncio.fixture
async def s3_connection(
    s3_for_worker: S3ConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    group: Group,
):
    s3 = s3_for_worker
    syncmaster_conn = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        type=s3.type,
        data=dict(
            host=s3.host,
            port=s3.port,
            bucket=s3.bucket,
            bucket_style=s3.bucket_style,
            region=s3.region,
            protocol=s3.protocol,
            additional_params=s3.additional_params,
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=syncmaster_conn.id,
        auth_data=dict(
            type="s3",
            access_key=s3.access_key,
            secret_key=s3.secret_key,
        ),
    )

    yield syncmaster_conn
    await session.delete(syncmaster_conn)
    await session.commit()
