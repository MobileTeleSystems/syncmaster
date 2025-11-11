import logging
import secrets

import pytest
import pytest_asyncio
from onetl.connection import MSSQL
from onetl.db import DBWriter
from pyspark.sql import DataFrame, SparkSession
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Group
from syncmaster.dto.connections import MSSQLConnectionDTO
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.settings import TestSettings
from tests.test_unit.utils import create_connection, create_credentials

logger = logging.getLogger(__name__)


@pytest.fixture(
    scope="session",
    params=[pytest.param("mssql", marks=[pytest.mark.mssql])],
)
def mssql_for_conftest(test_settings: TestSettings) -> MSSQLConnectionDTO:
    return MSSQLConnectionDTO(
        host=test_settings.TEST_MSSQL_HOST_FOR_CONFTEST,
        port=test_settings.TEST_MSSQL_PORT_FOR_CONFTEST,
        user=test_settings.TEST_MSSQL_USER,
        password=test_settings.TEST_MSSQL_PASSWORD,
        database_name=test_settings.TEST_MSSQL_DB,
        additional_params=test_settings.TEST_MSSQL_ADDITIONAL_PARAMS,
    )


@pytest.fixture(
    scope="session",
    params=[pytest.param("mssql", marks=[pytest.mark.mssql])],
)
def mssql_for_worker(test_settings: TestSettings) -> MSSQLConnectionDTO:
    return MSSQLConnectionDTO(
        host=test_settings.TEST_MSSQL_HOST_FOR_WORKER,
        port=test_settings.TEST_MSSQL_PORT_FOR_WORKER,
        user=test_settings.TEST_MSSQL_USER,
        password=test_settings.TEST_MSSQL_PASSWORD,
        database_name=test_settings.TEST_MSSQL_DB,
        additional_params=test_settings.TEST_MSSQL_ADDITIONAL_PARAMS,
    )


@pytest.fixture
def prepare_mssql(
    mssql_for_conftest: MSSQLConnectionDTO,
    spark: SparkSession,
):
    mssql = mssql_for_conftest
    onetl_conn = MSSQL(
        host=mssql.host,
        port=mssql.port,
        user=mssql.user,
        password=mssql.password,
        database=mssql.database_name,
        extra={"trustServerCertificate": "true"},
        spark=spark,
    ).check()
    try:
        onetl_conn.execute(f"DROP TABLE dbo.source_table")
    except Exception:
        pass
    try:
        onetl_conn.execute(f"DROP TABLE dbo.target_table")
    except Exception:
        pass

    def fill_with_data(df: DataFrame):
        logger.info("START PREPARE MSSQL")
        db_writer = DBWriter(
            connection=onetl_conn,
            target="dbo.source_table",
        )
        db_writer.run(df)
        logger.info("END PREPARE MSSQL")

    yield onetl_conn, fill_with_data

    try:
        onetl_conn.execute(f"DROP TABLE dbo.source_table")
    except Exception:
        pass
    try:
        onetl_conn.execute(f"DROP TABLE dbo.target_table")
    except Exception:
        pass


@pytest_asyncio.fixture
async def mssql_connection(
    mssql_for_worker: MSSQLConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    group: Group,
):
    mssql = mssql_for_worker
    syncmaster_conn = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        type=mssql.type,
        data=dict(
            host=mssql.host,
            port=mssql.port,
            database_name=mssql.database_name,
            additional_params=mssql.additional_params,
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=syncmaster_conn.id,
        auth_data=dict(
            type="basic",
            user=mssql.user,
            password=mssql.password,
        ),
    )

    yield syncmaster_conn
    await session.delete(syncmaster_conn)
    await session.commit()
