import logging
import secrets
from pathlib import PurePosixPath

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Group
from syncmaster.dto.connections import FTPSConnectionDTO
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.settings import TestSettings
from tests.test_unit.utils import create_connection, create_credentials, upload_files

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture
async def ftps_connection(
    ftps_for_worker: FTPSConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    group: Group,
):
    result = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        type=ftps_for_worker.type,
        data=dict(
            host=ftps_for_worker.host,
            port=ftps_for_worker.port,
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=result.id,
        auth_data=dict(
            type="basic",
            user=ftps_for_worker.user,
            password=ftps_for_worker.password,
        ),
    )

    yield result
    await session.delete(result)
    await session.commit()


@pytest.fixture(
    scope="session",
    params=[pytest.param("ftps", marks=[pytest.mark.ftps])],
)
def ftps_for_conftest(test_settings: TestSettings) -> FTPSConnectionDTO:
    return FTPSConnectionDTO(
        host=test_settings.TEST_FTPS_HOST_FOR_CONFTEST,
        port=test_settings.TEST_FTPS_PORT_FOR_CONFTEST,
        user=test_settings.TEST_FTPS_USER,
        password=test_settings.TEST_FTPS_PASSWORD,
    )


@pytest.fixture(
    scope="session",
    params=[pytest.param("ftps", marks=[pytest.mark.ftps])],
)
def ftps_for_worker(test_settings: TestSettings) -> FTPSConnectionDTO:
    return FTPSConnectionDTO(
        host=test_settings.TEST_FTPS_HOST_FOR_WORKER,
        port=test_settings.TEST_FTPS_PORT_FOR_WORKER,
        user=test_settings.TEST_FTPS_USER,
        password=test_settings.TEST_FTPS_PASSWORD,
    )


@pytest.fixture(scope="session")
def ftps_file_connection(ftps_for_conftest):
    from onetl.connection import FTPS

    return FTPS(
        host=ftps_for_conftest.host,
        port=ftps_for_conftest.port,
        user=ftps_for_conftest.user,
        password=ftps_for_conftest.password,
    )


@pytest.fixture
def ftps_file_connection_with_path(request, ftps_file_connection):
    connection = ftps_file_connection
    source = PurePosixPath("/data")
    target = PurePosixPath("/target")

    connection.remove_dir(source, recursive=True)
    connection.remove_dir(target, recursive=True)
    connection.create_dir(source)

    yield connection, source

    connection.remove_dir(source, recursive=True)
    connection.remove_dir(target, recursive=True)


@pytest.fixture(scope="session")
def ftps_file_df_connection(spark):
    from onetl.connection import SparkLocalFS

    return SparkLocalFS(spark=spark)


@pytest.fixture
def ftps_file_df_connection_with_path(ftps_file_connection_with_path, ftps_file_df_connection):
    _, source = ftps_file_connection_with_path
    return ftps_file_df_connection, source


@pytest.fixture
def prepare_ftps(
    ftps_file_df_connection_with_path,
    ftps_file_connection,
    resource_path,
):
    logger.info("START PREPARE FTPS")
    connection, upload_to = ftps_file_df_connection_with_path
    files = upload_files(resource_path, upload_to, ftps_file_connection)
    logger.info("END PREPARE FTPS")
    return connection, upload_to, files
