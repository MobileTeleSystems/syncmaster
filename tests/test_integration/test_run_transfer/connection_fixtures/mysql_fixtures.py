import logging
import secrets

import pytest
import pytest_asyncio
from onetl.connection import MySQL
from onetl.db import DBWriter
from pyspark.sql import DataFrame, SparkSession
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Group
from syncmaster.dto.connections import MySQLConnectionDTO
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.settings import TestSettings
from tests.test_unit.utils import create_connection, create_credentials

logger = logging.getLogger(__name__)


@pytest.fixture(
    scope="session",
    params=[pytest.param("mysql", marks=[pytest.mark.mysql])],
)
def mysql_for_conftest(test_settings: TestSettings) -> MySQLConnectionDTO:
    return MySQLConnectionDTO(
        host=test_settings.TEST_MYSQL_HOST_FOR_CONFTEST,
        port=test_settings.TEST_MYSQL_PORT_FOR_CONFTEST,
        user=test_settings.TEST_MYSQL_USER,
        password=test_settings.TEST_MYSQL_PASSWORD,
        database_name=test_settings.TEST_MYSQL_DB,
        additional_params={},
    )


@pytest.fixture(
    scope="session",
    params=[pytest.param("mysql", marks=[pytest.mark.mysql])],
)
def mysql_for_worker(test_settings: TestSettings) -> MySQLConnectionDTO:
    return MySQLConnectionDTO(
        host=test_settings.TEST_MYSQL_HOST_FOR_WORKER,
        port=test_settings.TEST_MYSQL_PORT_FOR_WORKER,
        user=test_settings.TEST_MYSQL_USER,
        password=test_settings.TEST_MYSQL_PASSWORD,
        database_name=test_settings.TEST_MYSQL_DB,
        additional_params={},
    )


@pytest.fixture
def prepare_mysql(
    mysql_for_conftest: MySQLConnectionDTO,
    spark: SparkSession,
):
    mysql = mysql_for_conftest
    onetl_conn = MySQL(
        host=mysql.host,
        port=mysql.port,
        user=mysql.user,
        password=mysql.password,
        database=mysql.database_name,
        spark=spark,
    ).check()
    try:
        onetl_conn.execute(f"DROP TABLE IF EXISTS {mysql.database_name}.source_table")
    except Exception:
        pass
    try:
        onetl_conn.execute(f"DROP TABLE IF EXISTS {mysql.database_name}.target_table")
    except Exception:
        pass

    def fill_with_data(df: DataFrame):
        logger.info("START PREPARE MYSQL")
        db_writer = DBWriter(
            connection=onetl_conn,
            target=f"{mysql.database_name}.source_table",
        )
        db_writer.run(df)
        logger.info("END PREPARE MYSQL")

    yield onetl_conn, fill_with_data

    try:
        onetl_conn.execute(f"DROP TABLE IF EXISTS {mysql.database_name}.source_table")
    except Exception:
        pass
    try:
        onetl_conn.execute(f"DROP TABLE IF EXISTS {mysql.database_name}.target_table")
    except Exception:
        pass


@pytest_asyncio.fixture
async def mysql_connection(
    mysql_for_worker: MySQLConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    group: Group,
):
    mysql = mysql_for_worker
    syncmaster_conn = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        type=mysql.type,
        data=dict(
            host=mysql.host,
            port=mysql.port,
            database_name=mysql.database_name,
            additional_params={},
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=syncmaster_conn.id,
        auth_data=dict(
            type="basic",
            user=mysql.user,
            password=mysql.password,
        ),
    )

    yield syncmaster_conn
    await session.delete(syncmaster_conn)
    await session.commit()
