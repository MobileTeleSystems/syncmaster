import logging
import secrets

import pytest
import pytest_asyncio
from onetl.connection import Postgres
from onetl.db import DBWriter
from pyspark.sql import DataFrame, SparkSession
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Group
from syncmaster.dto.connections import PostgresConnectionDTO
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.settings import TestSettings
from tests.test_unit.utils import create_connection, create_credentials

logger = logging.getLogger(__name__)


@pytest.fixture(
    scope="session",
    params=[pytest.param("postgres", marks=[pytest.mark.postgres])],
)
def postgres_for_conftest(test_settings: TestSettings) -> PostgresConnectionDTO:
    return PostgresConnectionDTO(
        host=test_settings.TEST_POSTGRES_HOST_FOR_CONFTEST,
        port=test_settings.TEST_POSTGRES_PORT_FOR_CONFTEST,
        user=test_settings.TEST_POSTGRES_USER,
        password=test_settings.TEST_POSTGRES_PASSWORD,
        database_name=test_settings.TEST_POSTGRES_DB,
        additional_params=test_settings.TEST_POSTGRES_ADDITIONAL_PARAMS,
    )


@pytest.fixture(
    scope="session",
    params=[pytest.param("postgres", marks=[pytest.mark.postgres])],
)
def postgres_for_worker(test_settings: TestSettings) -> PostgresConnectionDTO:
    return PostgresConnectionDTO(
        host=test_settings.TEST_POSTGRES_HOST_FOR_WORKER,
        port=test_settings.TEST_POSTGRES_PORT_FOR_WORKER,
        user=test_settings.TEST_POSTGRES_USER,
        password=test_settings.TEST_POSTGRES_PASSWORD,
        database_name=test_settings.TEST_POSTGRES_DB,
        additional_params=test_settings.TEST_POSTGRES_ADDITIONAL_PARAMS,
    )


@pytest.fixture
def prepare_postgres(
    spark: SparkSession,
    postgres_for_conftest: PostgresConnectionDTO,
):
    postgres = postgres_for_conftest
    onetl_conn = Postgres(
        host=postgres.host,
        port=postgres.port,
        user=postgres.user,
        password=postgres.password,
        database=postgres.database_name,
        spark=spark,
    ).check()
    onetl_conn.execute("DROP TABLE IF EXISTS public.source_table")
    onetl_conn.execute("DROP TABLE IF EXISTS public.target_table")

    def fill_with_data(df: DataFrame):
        logger.info("START PREPARE POSTGRES")
        db_writer = DBWriter(
            connection=onetl_conn,
            target="public.source_table",
            options=Postgres.WriteOptions(if_exists="append"),
        )
        db_writer.run(df)
        logger.info("END PREPARE POSTGRES")

    yield onetl_conn, fill_with_data
    onetl_conn.execute("DROP TABLE IF EXISTS public.source_table")
    onetl_conn.execute("DROP TABLE IF EXISTS public.target_table")


@pytest_asyncio.fixture
async def postgres_connection(
    postgres_for_worker: PostgresConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    group: Group,
):
    postgres = postgres_for_worker
    syncmaster_conn = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        type=postgres.type,
        data=dict(
            host=postgres.host,
            port=postgres.port,
            database_name=postgres.database_name,
            additional_params=postgres.additional_params,
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=syncmaster_conn.id,
        auth_data=dict(
            type="basic",
            user=postgres.user,
            password=postgres.password,
        ),
    )

    yield syncmaster_conn
    await session.delete(syncmaster_conn)
    await session.commit()
