import logging
import secrets

import pytest
import pytest_asyncio
from onetl.connection import Oracle
from onetl.db import DBWriter
from pyspark.sql import DataFrame, SparkSession
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Group
from syncmaster.dto.connections import OracleConnectionDTO
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.settings import TestSettings
from tests.test_unit.utils import create_connection, create_credentials

logger = logging.getLogger(__name__)


@pytest.fixture(
    scope="session",
    params=[pytest.param("oracle", marks=[pytest.mark.oracle])],
)
def oracle_for_conftest(test_settings: TestSettings) -> OracleConnectionDTO:
    return OracleConnectionDTO(
        host=test_settings.TEST_ORACLE_HOST_FOR_CONFTEST,
        port=test_settings.TEST_ORACLE_PORT_FOR_CONFTEST,
        user=test_settings.TEST_ORACLE_USER,
        password=test_settings.TEST_ORACLE_PASSWORD,
        service_name=test_settings.TEST_ORACLE_SERVICE_NAME,
        sid=test_settings.TEST_ORACLE_SID,
        additional_params={},
    )


@pytest.fixture(
    scope="session",
    params=[pytest.param("oracle", marks=[pytest.mark.oracle])],
)
def oracle_for_worker(test_settings: TestSettings) -> OracleConnectionDTO:
    return OracleConnectionDTO(
        host=test_settings.TEST_ORACLE_HOST_FOR_WORKER,
        port=test_settings.TEST_ORACLE_PORT_FOR_WORKER,
        user=test_settings.TEST_ORACLE_USER,
        password=test_settings.TEST_ORACLE_PASSWORD,
        service_name=test_settings.TEST_ORACLE_SERVICE_NAME,
        sid=test_settings.TEST_ORACLE_SID,
        additional_params={},
    )


@pytest.fixture
def prepare_oracle(
    oracle_for_conftest: OracleConnectionDTO,
    spark: SparkSession,
):
    oracle = oracle_for_conftest
    onetl_conn = Oracle(
        host=oracle.host,
        port=oracle_for_conftest.port,
        user=oracle.user,
        password=oracle.password,
        sid=oracle.sid,
        service_name=oracle.service_name,
        spark=spark,
    ).check()
    try:
        onetl_conn.execute(f"DROP TABLE {oracle.user}.source_table")
    except Exception:
        pass
    try:
        onetl_conn.execute(f"DROP TABLE {oracle.user}.target_table")
    except Exception:
        pass

    def fill_with_data(df: DataFrame):
        logger.info("START PREPARE ORACLE")
        db_writer = DBWriter(
            connection=onetl_conn,
            target=f"{oracle.user}.source_table",
            options=Oracle.WriteOptions(if_exists="append"),
        )
        db_writer.run(df)
        logger.info("END PREPARE ORACLE")

    yield onetl_conn, fill_with_data

    try:
        onetl_conn.execute(f"DROP TABLE {oracle.user}.source_table")
    except Exception:
        pass
    try:
        onetl_conn.execute(f"DROP TABLE {oracle.user}.target_table")
    except Exception:
        pass


@pytest_asyncio.fixture
async def oracle_connection(
    oracle_for_worker: OracleConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    group: Group,
):
    oracle = oracle_for_worker
    syncmaster_conn = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        type=oracle.type,
        data=dict(
            host=oracle.host,
            port=oracle.port,
            sid=oracle.sid,
            service_name=oracle.service_name,
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
            user=oracle.user,
            password=oracle.password,
        ),
    )

    yield syncmaster_conn
    await session.delete(syncmaster_conn)
    await session.commit()
