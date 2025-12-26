import logging
import secrets
from pathlib import PurePosixPath

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Group
from syncmaster.dto.connections import SambaConnectionDTO
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.settings import TestSettings
from tests.test_unit.utils import create_connection, create_credentials, upload_files

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture
async def samba_connection(
    samba_for_worker: SambaConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    group: Group,
):
    result = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        type=samba_for_worker.type,
        data=dict(
            host=samba_for_worker.host,
            share=samba_for_worker.share,
            protocol=samba_for_worker.protocol,
            domain=samba_for_worker.domain,
            port=samba_for_worker.port,
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=result.id,
        auth_data=dict(
            type="samba",
            user=samba_for_worker.user,
            password=samba_for_worker.password,
            auth_type=samba_for_worker.auth_type,
        ),
    )

    yield result
    await session.delete(result)
    await session.commit()


@pytest.fixture(
    scope="session",
    params=[pytest.param("samba", marks=[pytest.mark.samba])],
)
def samba_for_conftest(test_settings: TestSettings) -> SambaConnectionDTO:
    return SambaConnectionDTO(
        host=test_settings.TEST_SAMBA_HOST_FOR_CONFTEST,
        port=test_settings.TEST_SAMBA_PORT_FOR_CONFTEST,
        share=test_settings.TEST_SAMBA_SHARE,
        protocol=test_settings.TEST_SAMBA_PROTOCOL,
        domain=test_settings.TEST_SAMBA_DOMAIN,
        user=test_settings.TEST_SAMBA_USER,
        password=test_settings.TEST_SAMBA_PASSWORD,
        auth_type=test_settings.TEST_SAMBA_AUTH_TYPE,
    )


@pytest.fixture(
    scope="session",
    params=[pytest.param("samba", marks=[pytest.mark.samba])],
)
def samba_for_worker(test_settings: TestSettings) -> SambaConnectionDTO:
    return SambaConnectionDTO(
        host=test_settings.TEST_SAMBA_HOST_FOR_WORKER,
        port=test_settings.TEST_SAMBA_PORT_FOR_WORKER,
        share=test_settings.TEST_SAMBA_SHARE,
        protocol=test_settings.TEST_SAMBA_PROTOCOL,
        domain=test_settings.TEST_SAMBA_DOMAIN,
        user=test_settings.TEST_SAMBA_USER,
        password=test_settings.TEST_SAMBA_PASSWORD,
        auth_type=test_settings.TEST_SAMBA_AUTH_TYPE,
    )


@pytest.fixture(scope="session")
def samba_file_connection(samba_for_conftest):
    from onetl.connection import Samba

    return Samba(
        host=samba_for_conftest.host,
        port=samba_for_conftest.port,
        share=samba_for_conftest.share,
        protocol=samba_for_conftest.protocol,
        domain=samba_for_conftest.domain,
        user=samba_for_conftest.user,
        password=samba_for_conftest.password,
        auth_type=samba_for_conftest.auth_type,
    )


@pytest.fixture
def samba_file_connection_with_path(samba_file_connection):
    connection = samba_file_connection
    source = PurePosixPath("/data")
    target = PurePosixPath("/target")

    connection.remove_dir(source, recursive=True)
    connection.remove_dir(target, recursive=True)
    connection.create_dir(source)

    yield connection, source

    connection.remove_dir(source, recursive=True)
    connection.remove_dir(target, recursive=True)


@pytest.fixture(scope="session")
def samba_file_df_connection(spark):
    from onetl.connection import SparkLocalFS

    return SparkLocalFS(spark=spark)


@pytest.fixture
def samba_file_df_connection_with_path(samba_file_connection_with_path, samba_file_df_connection):
    _, source = samba_file_connection_with_path
    return samba_file_df_connection, source


@pytest.fixture
def prepare_samba(
    samba_file_df_connection_with_path,
    samba_file_connection,
    resource_path,
):
    logger.info("START PREPARE SAMBA")
    connection, upload_to = samba_file_df_connection_with_path
    files = upload_files(resource_path, upload_to, samba_file_connection)
    logger.info("END PREPARE SAMBA")
    return connection, upload_to, files
