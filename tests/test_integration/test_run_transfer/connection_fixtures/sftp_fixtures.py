import logging
import secrets
from pathlib import PurePosixPath

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Group
from syncmaster.dto.connections import SFTPConnectionDTO
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.settings import TestSettings
from tests.test_unit.utils import create_connection, create_credentials, upload_files

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture
async def sftp_connection(
    sftp_for_worker: SFTPConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    group: Group,
):
    result = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        type=sftp_for_worker.type,
        data=dict(
            host=sftp_for_worker.host,
            port=sftp_for_worker.port,
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=result.id,
        auth_data=dict(
            type="basic",
            user=sftp_for_worker.user,
            password=sftp_for_worker.password,
        ),
    )

    yield result
    await session.delete(result)
    await session.commit()


@pytest.fixture(
    scope="session",
    params=[pytest.param("sftp", marks=[pytest.mark.sftp])],
)
def sftp_for_conftest(test_settings: TestSettings) -> SFTPConnectionDTO:
    return SFTPConnectionDTO(
        host=test_settings.TEST_SFTP_HOST_FOR_CONFTEST,
        port=test_settings.TEST_SFTP_PORT_FOR_CONFTEST,
        user=test_settings.TEST_SFTP_USER,
        password=test_settings.TEST_SFTP_PASSWORD,
    )


@pytest.fixture(
    scope="session",
    params=[pytest.param("sftp", marks=[pytest.mark.sftp])],
)
def sftp_for_worker(test_settings: TestSettings) -> SFTPConnectionDTO:
    return SFTPConnectionDTO(
        host=test_settings.TEST_SFTP_HOST_FOR_WORKER,
        port=test_settings.TEST_SFTP_PORT_FOR_WORKER,
        user=test_settings.TEST_SFTP_USER,
        password=test_settings.TEST_SFTP_PASSWORD,
    )


@pytest.fixture(scope="session")
def sftp_file_connection(sftp_for_conftest):
    from onetl.connection import SFTP

    return SFTP(
        host=sftp_for_conftest.host,
        port=sftp_for_conftest.port,
        user=sftp_for_conftest.user,
        password=sftp_for_conftest.password,
        compress=False,
    )


@pytest.fixture()
def sftp_file_connection_with_path(request, sftp_file_connection):
    connection = sftp_file_connection
    source = PurePosixPath("/config/data")
    target = PurePosixPath("/config/target")

    def finalizer():
        connection.remove_dir(source, recursive=True)
        connection.remove_dir(target, recursive=True)

    request.addfinalizer(finalizer)

    connection.remove_dir(source, recursive=True)
    connection.remove_dir(target, recursive=True)
    connection.create_dir(source)

    return connection, source


@pytest.fixture(scope="session")
def sftp_file_df_connection(spark):
    from onetl.connection import SparkLocalFS

    return SparkLocalFS(spark=spark)


@pytest.fixture()
def sftp_file_df_connection_with_path(sftp_file_connection_with_path, sftp_file_df_connection):
    _, source = sftp_file_connection_with_path
    return sftp_file_df_connection, source


@pytest.fixture()
def prepare_sftp(
    sftp_file_df_connection_with_path,
    sftp_file_connection,
    resource_path,
):
    logger.info("START PREPARE SFTP")
    connection, upload_to = sftp_file_df_connection_with_path
    files = upload_files(resource_path, upload_to, sftp_file_connection)
    logger.info("END PREPARE SFTP")
    return connection, upload_to, files
