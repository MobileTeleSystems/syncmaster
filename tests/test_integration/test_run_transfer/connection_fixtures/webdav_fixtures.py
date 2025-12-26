import logging
import secrets
from pathlib import PurePosixPath

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Group
from syncmaster.dto.connections import WebDAVConnectionDTO
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.settings import TestSettings
from tests.test_unit.utils import create_connection, create_credentials, upload_files

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture
async def webdav_connection(
    webdav_for_worker: WebDAVConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    group: Group,
):
    result = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        type=webdav_for_worker.type,
        data=dict(
            host=webdav_for_worker.host,
            port=webdav_for_worker.port,
            protocol=webdav_for_worker.protocol,
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=result.id,
        auth_data=dict(
            type="basic",
            user=webdav_for_worker.user,
            password=webdav_for_worker.password,
        ),
    )

    yield result
    await session.delete(result)
    await session.commit()


@pytest.fixture(
    scope="session",
    params=[pytest.param("webdav", marks=[pytest.mark.webdav])],
)
def webdav_for_conftest(test_settings: TestSettings) -> WebDAVConnectionDTO:
    return WebDAVConnectionDTO(
        host=test_settings.TEST_WEBDAV_HOST_FOR_CONFTEST,
        port=test_settings.TEST_WEBDAV_PORT_FOR_CONFTEST,
        protocol=test_settings.TEST_WEBDAV_PROTOCOL,
        user=test_settings.TEST_WEBDAV_USER,
        password=test_settings.TEST_WEBDAV_PASSWORD,
    )


@pytest.fixture(
    scope="session",
    params=[pytest.param("webdav", marks=[pytest.mark.webdav])],
)
def webdav_for_worker(test_settings: TestSettings) -> WebDAVConnectionDTO:
    return WebDAVConnectionDTO(
        host=test_settings.TEST_WEBDAV_HOST_FOR_WORKER,
        port=test_settings.TEST_WEBDAV_PORT_FOR_WORKER,
        protocol=test_settings.TEST_WEBDAV_PROTOCOL,
        user=test_settings.TEST_WEBDAV_USER,
        password=test_settings.TEST_WEBDAV_PASSWORD,
    )


@pytest.fixture(scope="session")
def webdav_file_connection(webdav_for_conftest):
    from onetl.connection import WebDAV

    return WebDAV(
        host=webdav_for_conftest.host,
        port=webdav_for_conftest.port,
        protocol=webdav_for_conftest.protocol,
        user=webdav_for_conftest.user,
        password=webdav_for_conftest.password,
        ssl_verify=False,
    )


@pytest.fixture
def webdav_file_connection_with_path(webdav_file_connection):
    connection = webdav_file_connection
    source = PurePosixPath("/data")
    target = PurePosixPath("/target")

    connection.remove_dir(source, recursive=True)
    connection.remove_dir(target, recursive=True)
    connection.create_dir(source)

    yield connection, source

    connection.remove_dir(source, recursive=True)
    connection.remove_dir(target, recursive=True)


@pytest.fixture(scope="session")
def webdav_file_df_connection(spark):
    from onetl.connection import SparkLocalFS

    return SparkLocalFS(spark=spark)


@pytest.fixture
def webdav_file_df_connection_with_path(webdav_file_connection_with_path, webdav_file_df_connection):
    _, source = webdav_file_connection_with_path
    return webdav_file_df_connection, source


@pytest.fixture
def prepare_webdav(
    webdav_file_df_connection_with_path,
    webdav_file_connection,
    resource_path,
):
    logger.info("START PREPARE WEBDAV")
    connection, upload_to = webdav_file_df_connection_with_path
    files = upload_files(resource_path, upload_to, webdav_file_connection)
    logger.info("END PREPARE WEBDAV")
    return connection, upload_to, files
