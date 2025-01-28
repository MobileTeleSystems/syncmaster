import logging
import secrets

import pytest
import pytest_asyncio
from onetl.connection import Hive
from onetl.db import DBWriter
from pyspark.sql import DataFrame, SparkSession
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Group
from syncmaster.dto.connections import HiveConnectionDTO
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.settings import TestSettings
from tests.test_unit.utils import create_connection, create_credentials

logger = logging.getLogger(__name__)


@pytest.fixture(
    scope="session",
    params=[pytest.param("hive", marks=[pytest.mark.hive])],
)
def hive(test_settings: TestSettings) -> HiveConnectionDTO:
    return HiveConnectionDTO(
        cluster=test_settings.TEST_HIVE_CLUSTER,
        user=test_settings.TEST_HIVE_USER,
        password=test_settings.TEST_HIVE_PASSWORD,
    )


@pytest.fixture
def prepare_hive(
    spark: SparkSession,
    hive: HiveConnectionDTO,
):
    result = Hive(
        cluster=hive.cluster,
        spark=spark,
    ).check()
    result.execute("DROP TABLE IF EXISTS default.source_table")
    result.execute("DROP TABLE IF EXISTS default.target_table")
    result.execute("CREATE DATABASE IF NOT EXISTS default")

    def fill_with_data(df: DataFrame):
        logger.info("START PREPARE HIVE")
        db_writer = DBWriter(
            connection=result,
            target="default.source_table",
        )
        db_writer.run(df)
        spark.catalog.refreshTable("default.source_table")
        logger.info("END PREPARE HIVE")

    yield result, fill_with_data

    result.execute("DROP TABLE IF EXISTS default.source_table")
    result.execute("DROP TABLE IF EXISTS default.target_table")


@pytest_asyncio.fixture
async def hive_connection(
    hive: HiveConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    group: Group,
):
    result = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        type=hive.type,
        data=dict(
            cluster=hive.cluster,
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=result.id,
        auth_data=dict(
            type="basic",
            user=hive.user,
            password=hive.password,
        ),
    )

    yield result
    await session.delete(result)
    await session.commit()
