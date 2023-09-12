import os
from datetime import date, datetime

import pytest
import pytest_asyncio
from onetl.connection import Oracle, Postgres
from onetl.db import DBWriter
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    DateType,
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_unit.utils import create_connection, create_transfer, create_user
from tests.utils import MockUser

from app.api.v1.auth.utils import sign_jwt
from app.config import Settings
from app.dto.connections import OracleConnectionDTO, PostgresConnectionDTO


@pytest.fixture
def spark(settings: Settings):
    return settings.CREATE_SPARK_SESSION_FUNCTION(settings)


@pytest.fixture
def postgres() -> PostgresConnectionDTO:
    return PostgresConnectionDTO(
        type="postgres",
        host=os.environ.get("TEST_POSTGRES_HOST", "127.0.0.1"),
        port=int(os.environ.get("TEST_POSTGRES_PORT", 5432)),
        user=os.environ.get("TEST_POSTGRES_USER", "user"),
        password=os.environ.get("TEST_POSTGRES_PASSWORD", "password"),
        database_name=os.environ.get("TEST_POSTGRES_DB", "test_db"),
        additional_params={},
    )


@pytest.fixture
def oracle() -> OracleConnectionDTO:
    return OracleConnectionDTO(
        type="oracle",
        host=os.environ.get("TEST_ORACLE_HOST", "127.0.0.1"),
        port=int(os.environ.get("TEST_ORACLE_PORT", 1521)),
        user=os.environ.get("TEST_ORACLE_USER", "user"),
        password=os.environ.get("TEST_ORACLE_PASSWORD", "password"),
        service_name=os.environ.get("TEST_ORACLE_SERVICE_NAME", "XEPDB1"),
        sid=None,
        additional_params={},
    )


@pytest.fixture
def init_df(spark: SparkSession) -> DataFrame:
    df_schema = StructType(
        [
            StructField("ID", IntegerType()),
            StructField("PHONE_NUMBER", StringType()),
            StructField("REGION", StringType()),
            StructField("BIRTH_DATE", DateType()),
            StructField("REGISTERED_AT", TimestampType()),
            StructField("ACCOUNT_BALANCE", DoubleType()),
        ],
    )
    df_to_write = spark.createDataFrame(
        data=[
            {
                "ID": 1,
                "PHONE_NUMBER": "+79123456789",
                "REGION": "Mordor",
                "BIRTH_DATE": date(year=2023, month=3, day=11),
                "REGISTERED_AT": datetime.now(),
                "ACCOUNT_BALANCE": 1234.2343,
            },
            {
                "ID": 2,
                "PHONE_NUMBER": "+79123456789",
                "REGION": "Mordor",
                "BIRTH_DATE": date(year=2023, month=3, day=11),
                "REGISTERED_AT": datetime.now(),
                "ACCOUNT_BALANCE": 1234.2343,
            },
            {
                "ID": 3,
                "PHONE_NUMBER": "+79123456789",
                "REGION": "Mordor",
                "BIRTH_DATE": date(year=2023, month=3, day=11),
                "REGISTERED_AT": datetime.now(),
                "ACCOUNT_BALANCE": 1234.2343,
            },
            {
                "ID": 4,
                "PHONE_NUMBER": "+79123456789",
                "REGION": "Mordor",
                "BIRTH_DATE": date(year=2023, month=3, day=11),
                "REGISTERED_AT": datetime.now(),
                "ACCOUNT_BALANCE": 1234.2343,
            },
            {
                "ID": 5,
                "PHONE_NUMBER": "+79123456789",
                "REGION": "Mordor",
                "BIRTH_DATE": date(year=2023, month=3, day=11),
                "REGISTERED_AT": datetime.now(),
                "ACCOUNT_BALANCE": 1234.2343,
            },
        ],
        schema=df_schema,
    )
    return df_to_write


@pytest.fixture
def prepare_postgres(
    spark: SparkSession, postgres: PostgresConnectionDTO, init_df: DataFrame
) -> Postgres:
    postgres_connection = Postgres(
        host=postgres.host,
        port=postgres.port,
        user=postgres.user,
        password=postgres.password,
        database=postgres.database_name,
        spark=spark,
    ).check()
    postgres_connection.execute(f"DROP TABLE IF EXISTS public.source_table")
    postgres_connection.execute(f"DROP TABLE IF EXISTS public.target_table")
    db_writer = DBWriter(
        connection=postgres_connection,
        target="public.source_table",
        options=Postgres.WriteOptions(if_exists="append"),
    )
    db_writer.run(init_df)
    return postgres_connection


@pytest.fixture
def prepare_oracle(
    spark: SparkSession, oracle: OracleConnectionDTO, init_df: DataFrame
) -> Oracle:
    oracle_connection = Oracle(
        host=oracle.host,
        port=oracle.port,
        user=oracle.user,
        password=oracle.password,
        sid=oracle.sid,
        service_name=oracle.service_name,
        spark=spark,
    ).check()
    try:
        oracle_connection.execute(f"DROP TABLE {oracle.user}.source_table")
    except Exception:
        pass
    try:
        oracle_connection.execute(f"DROP TABLE {oracle.user}.target_table")
    except Exception:
        pass
    db_writer = DBWriter(
        connection=oracle_connection,
        target=f"{oracle.user}.source_table",
        options=Oracle.WriteOptions(if_exists="append"),
    )
    db_writer.run(init_df)
    return oracle_connection


@pytest_asyncio.fixture
async def transfers(
    prepare_postgres,
    prepare_oracle,
    postgres: PostgresConnectionDTO,
    oracle: OracleConnectionDTO,
    session: AsyncSession,
    settings: Settings,
):
    user = await create_user(
        session=session, username="connection_owner", is_active=True
    )
    postgres_connection = await create_connection(
        session=session,
        name="integration_postgres",
        user_id=user.id,
        data=dict(
            type=postgres.type,
            host=postgres.host,
            port=postgres.port,
            user=postgres.user,
            password=postgres.password,
            database_name=postgres.database_name,
            additional_params={},
        ),
    )
    oracle_connection = await create_connection(
        session=session,
        name="integration_oracle",
        user_id=user.id,
        data=dict(
            type=oracle.type,
            host=oracle.host,
            port=oracle.port,
            user=oracle.user,
            password=oracle.password,
            sid=oracle.sid,
            service_name=oracle.service_name,
            additional_params={},
        ),
    )

    postgres_oracle_transfer = await create_transfer(
        session=session,
        name="integration_transfer_postgres_oracle",
        source_connection_id=postgres_connection.id,
        target_connection_id=oracle_connection.id,
        user_id=user.id,
        source_params={
            "type": "postgres",
            "table_name": "public.source_table",
        },
        target_params={
            "type": "oracle",
            "table_name": f"{oracle.user}.target_table",
        },
    )

    oracle_postgres_transfer = await create_transfer(
        session=session,
        name="integration_transfer_oracle_postgres",
        source_connection_id=oracle_connection.id,
        target_connection_id=postgres_connection.id,
        user_id=user.id,
        source_params={
            "type": "oracle",
            "table_name": f"{oracle.user}.source_table",
        },
        target_params={
            "type": "postgres",
            "table_name": "public.target_table",
        },
    )

    yield {
        "owner": MockUser(user=user, auth_token=sign_jwt(user.id, settings)),
        "postgres_oracle": postgres_oracle_transfer,
        "oracle_postgres": oracle_postgres_transfer,
    }

    await session.delete(postgres_oracle_transfer)
    await session.delete(oracle_postgres_transfer)
    await session.delete(postgres_connection)
    await session.delete(oracle_connection)
    await session.delete(user)
    await session.commit()
