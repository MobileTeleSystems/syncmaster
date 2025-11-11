import logging
import secrets

import pytest
import pytest_asyncio
from onetl.connection import Clickhouse
from onetl.db import DBWriter
from pyspark.sql import DataFrame, SparkSession
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Group
from syncmaster.dto.connections import ClickhouseConnectionDTO
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.settings import TestSettings
from tests.test_unit.utils import create_connection, create_credentials

logger = logging.getLogger(__name__)


@pytest.fixture(
    scope="session",
    params=[pytest.param("clickhouse", marks=[pytest.mark.clickhouse])],
)
def clickhouse_for_conftest(test_settings: TestSettings) -> ClickhouseConnectionDTO:
    return ClickhouseConnectionDTO(
        host=test_settings.TEST_CLICKHOUSE_HOST_FOR_CONFTEST,
        port=test_settings.TEST_CLICKHOUSE_PORT_FOR_CONFTEST,
        user=test_settings.TEST_CLICKHOUSE_USER,
        password=test_settings.TEST_CLICKHOUSE_PASSWORD,
        database_name=test_settings.TEST_CLICKHOUSE_DB,
        additional_params=test_settings.TEST_CLICKHOUSE_ADDITIONAL_PARAMS,
    )


@pytest.fixture(
    scope="session",
    params=[pytest.param("clickhouse", marks=[pytest.mark.clickhouse])],
)
def clickhouse_for_worker(test_settings: TestSettings) -> ClickhouseConnectionDTO:
    return ClickhouseConnectionDTO(
        host=test_settings.TEST_CLICKHOUSE_HOST_FOR_WORKER,
        port=test_settings.TEST_CLICKHOUSE_PORT_FOR_WORKER,
        user=test_settings.TEST_CLICKHOUSE_USER,
        password=test_settings.TEST_CLICKHOUSE_PASSWORD,
        database_name=test_settings.TEST_CLICKHOUSE_DB,
        additional_params=test_settings.TEST_CLICKHOUSE_ADDITIONAL_PARAMS,
    )


@pytest.fixture
def prepare_clickhouse(
    clickhouse_for_conftest: ClickhouseConnectionDTO,
    spark: SparkSession,
):
    ClickhouseDialectRegistry = (
        spark._jvm.io.github.mtsongithub.doetl.sparkdialectextensions.clickhouse.ClickhouseDialectRegistry
    )
    ClickhouseDialectRegistry.register()

    clickhouse = clickhouse_for_conftest
    onetl_conn = Clickhouse(
        host=clickhouse.host,
        port=clickhouse.port,
        user=clickhouse.user,
        password=clickhouse.password,
        spark=spark,
    ).check()
    try:
        onetl_conn.execute(f"DROP TABLE {clickhouse.user}.source_table")
    except Exception:
        pass
    try:
        onetl_conn.execute(f"DROP TABLE {clickhouse.user}.target_table")
    except Exception:
        pass

    def fill_with_data(df: DataFrame):
        logger.info("START PREPARE CLICKHOUSE")
        db_writer = DBWriter(
            connection=onetl_conn,
            target=f"{clickhouse.user}.source_table",
            options=Clickhouse.WriteOptions(createTableOptions="ENGINE = Memory"),
        )
        db_writer.run(df)
        logger.info("END PREPARE CLICKHOUSE")

    yield onetl_conn, fill_with_data

    try:
        onetl_conn.execute(f"DROP TABLE {clickhouse.user}.source_table")
    except Exception:
        pass
    try:
        onetl_conn.execute(f"DROP TABLE {clickhouse.user}.target_table")
    except Exception:
        pass


@pytest_asyncio.fixture
async def clickhouse_connection(
    clickhouse_for_worker: ClickhouseConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    group: Group,
):
    clickhouse = clickhouse_for_worker
    syncmaster_conn = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        type=clickhouse.type,
        data=dict(
            host=clickhouse.host,
            port=clickhouse.port,
            database_name=clickhouse.database_name,
            additional_params=clickhouse.additional_params,
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=syncmaster_conn.id,
        auth_data=dict(
            type="basic",
            user=clickhouse.user,
            password=clickhouse.password,
        ),
    )

    yield syncmaster_conn
    await session.delete(syncmaster_conn)
    await session.commit()
