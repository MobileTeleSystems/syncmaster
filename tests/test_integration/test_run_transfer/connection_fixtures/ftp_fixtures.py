import logging
import secrets
from pathlib import PurePosixPath

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Group
from syncmaster.dto.connections import FTPConnectionDTO
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.settings import TestSettings
from tests.test_unit.utils import create_connection, create_credentials, upload_files

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture
async def ftp_connection(
    ftp_for_worker: FTPConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    group: Group,
):
    result = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        type=ftp_for_worker.type,
        data=dict(
            host=ftp_for_worker.host,
            port=ftp_for_worker.port,
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=result.id,
        auth_data=dict(
            type="basic",
            user=ftp_for_worker.user,
            password=ftp_for_worker.password,
        ),
    )

    yield result
    await session.delete(result)
    await session.commit()


@pytest.fixture(
    scope="session",
    params=[pytest.param("ftp", marks=[pytest.mark.ftp])],
)
def ftp_for_conftest(test_settings: TestSettings) -> FTPConnectionDTO:
    return FTPConnectionDTO(
        host=test_settings.TEST_FTP_HOST_FOR_CONFTEST,
        port=test_settings.TEST_FTP_PORT_FOR_CONFTEST,
        user=test_settings.TEST_FTP_USER,
        password=test_settings.TEST_FTP_PASSWORD,
    )


@pytest.fixture(
    scope="session",
    params=[pytest.param("ftp", marks=[pytest.mark.ftp])],
)
def ftp_for_worker(test_settings: TestSettings) -> FTPConnectionDTO:
    return FTPConnectionDTO(
        host=test_settings.TEST_FTP_HOST_FOR_WORKER,
        port=test_settings.TEST_FTP_PORT_FOR_WORKER,
        user=test_settings.TEST_FTP_USER,
        password=test_settings.TEST_FTP_PASSWORD,
    )


@pytest.fixture(scope="session")
def ftp_file_connection(ftp_for_conftest):
    from onetl.connection import FTP

    return FTP(
        host=ftp_for_conftest.host,
        port=ftp_for_conftest.port,
        user=ftp_for_conftest.user,
        password=ftp_for_conftest.password,
    )


@pytest.fixture()
def ftp_file_connection_with_path(request, ftp_file_connection):
    connection = ftp_file_connection
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


@pytest.fixture(scope="session")
def ftp_file_df_connection(spark):
    from onetl.connection import SparkLocalFS

    return SparkLocalFS(spark=spark)


@pytest.fixture()
def ftp_file_df_connection_with_path(ftp_file_connection_with_path, ftp_file_df_connection):
    _, source = ftp_file_connection_with_path
    return ftp_file_df_connection, source


@pytest.fixture()
def prepare_ftp(
    ftp_file_df_connection_with_path,
    ftp_file_connection,
    resource_path,
):
    logger.info("START PREPARE FTP")
    connection, upload_to = ftp_file_df_connection_with_path
    files = upload_files(resource_path, upload_to, ftp_file_connection)
    logger.info("END PREPARE FTP")
    return connection, upload_to, files
