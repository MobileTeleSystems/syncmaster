import os
from datetime import date, datetime
from itertools import permutations

import pytest
import pytest_asyncio
from onetl.connection import Hive, Oracle, Postgres
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
from tests.test_unit.utils import (
    create_connection,
    create_credentials,
    create_group,
    create_transfer,
    create_user,
)
from tests.utils import MockUser, TestUserRoles

from app.api.v1.auth.utils import sign_jwt
from app.config import EnvTypes, Settings, TestSettings
from app.dto.connections import (
    HiveConnectionDTO,
    OracleConnectionDTO,
    PostgresConnectionDTO,
)


@pytest.fixture
def spark(settings: Settings) -> SparkSession:
    return get_spark_session(settings)


def get_spark_session(connection_settings: Settings) -> SparkSession:
    maven_packages = [p for connection in (Postgres, Oracle) for p in connection.get_packages()]

    spark = (
        SparkSession.builder.appName("celery_worker")
        .config("spark.jars.packages", ",".join(maven_packages))
        .config("spark.sql.pyspark.jvmStacktrace.enabled", "true")
        .enableHiveSupport()
    )

    if connection_settings.ENV == EnvTypes.GITLAB:
        spark = spark.config(
            "spark.jars.ivySettings",
            os.fspath(connection_settings.IVYSETTINGS_PATH),
        )

    return spark.getOrCreate()


@pytest.fixture
def hive(test_settings: TestSettings) -> HiveConnectionDTO:
    return HiveConnectionDTO(
        type="hive",
        cluster=test_settings.TEST_HIVE_CLUSTER,
        additional_params={},
        user=test_settings.TEST_HIVE_USER,
        password=test_settings.TEST_HIVE_PASSWORD,
    )


@pytest.fixture
def oracle(test_settings: TestSettings) -> OracleConnectionDTO:
    return OracleConnectionDTO(
        type="oracle",
        host=test_settings.TEST_ORACLE_HOST,
        port=test_settings.TEST_ORACLE_PORT,
        user=test_settings.TEST_ORACLE_USER,
        password=test_settings.TEST_ORACLE_PASSWORD,
        service_name=test_settings.TEST_ORACLE_SERVICE_NAME,
        sid=test_settings.TEST_ORACLE_SID,
        additional_params={},
    )


@pytest.fixture
def postgres(test_settings: TestSettings) -> PostgresConnectionDTO:
    return PostgresConnectionDTO(
        type="postgres",
        host=test_settings.TEST_POSTGRES_HOST,
        port=test_settings.TEST_POSTGRES_PORT,
        user=test_settings.TEST_POSTGRES_USER,
        password=test_settings.TEST_POSTGRES_PASSWORD,
        database_name=test_settings.TEST_POSTGRES_DB,
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
    spark: SparkSession,
    postgres: PostgresConnectionDTO,
    init_df: DataFrame,
) -> Postgres:
    postgres_connection = Postgres(
        host=postgres.host,
        port=postgres.port,
        user=postgres.user,
        password=postgres.password,
        database=postgres.database_name,
        spark=spark,
    ).check()
    postgres_connection.execute("DROP TABLE IF EXISTS public.source_table")
    postgres_connection.execute("DROP TABLE IF EXISTS public.target_table")
    db_writer = DBWriter(
        connection=postgres_connection,
        target="public.source_table",
        options=Postgres.WriteOptions(if_exists="append"),
    )
    db_writer.run(init_df)
    return postgres_connection


@pytest.fixture
def prepare_hive(spark: SparkSession, hive: HiveConnectionDTO, init_df: DataFrame) -> Hive:
    hive_connection = Hive(
        cluster=hive.cluster,
        spark=spark,
    ).check()
    hive_connection.execute("DROP TABLE IF EXISTS public.source_table")
    hive_connection.execute("DROP TABLE IF EXISTS public.target_table")
    hive_connection.execute("CREATE DATABASE IF NOT EXISTS public")
    db_writer = DBWriter(
        connection=hive_connection,
        target="public.source_table",
    )
    db_writer.run(init_df)
    spark.catalog.refreshTable("public.source_table")
    return hive_connection


@pytest.fixture
def prepare_oracle(
    spark: SparkSession,
    oracle: OracleConnectionDTO,
    init_df: DataFrame,
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
    prepare_hive,
    postgres: PostgresConnectionDTO,
    oracle: OracleConnectionDTO,
    hive: HiveConnectionDTO,
    session: AsyncSession,
    settings: Settings,
):
    user = await create_user(
        session=session,
        username="admin_group",
        is_active=True,
    )
    group = await create_group(session=session, name="connection_group", admin_id=user.id)
    hive_connection = await create_connection(
        session=session,
        name="integration_hive",
        data=dict(
            type=hive.type,
            cluster=hive.cluster,
            additional_params={},
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=hive_connection.id,
        auth_data=dict(
            type="hive",
            user=hive.user,
            password=hive.password,
        ),
    )

    postgres_connection = await create_connection(
        session=session,
        name="integration_postgres",
        data=dict(
            type=postgres.type,
            host=postgres.host,
            port=postgres.port,
            database_name=postgres.database_name,
            additional_params={},
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=postgres_connection.id,
        auth_data=dict(
            type="postgres",
            user=postgres.user,
            password=postgres.password,
        ),
    )

    oracle_connection = await create_connection(
        session=session,
        name="integration_oracle",
        data=dict(
            type=oracle.type,
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
        connection_id=oracle_connection.id,
        auth_data=dict(
            type="oracle",
            user=oracle.user,
            password=oracle.password,
        ),
    )

    transfers = {}
    for source, target in permutations(
        [
            hive_connection,
            oracle_connection,
            postgres_connection,
        ],
        2,
    ):
        source_type = source.data["type"]
        target_type = target.data["type"]
        transfer = await create_transfer(
            session=session,
            group_id=group.id,
            name=f"integration_transfer_{source_type}_{target_type}",
            source_connection_id=source.id,
            target_connection_id=target.id,
            source_params={
                "type": source_type,
                "table_name": (oracle.user if source_type == "oracle" else "public") + ".source_table",
            },
            target_params={
                "type": target_type,
                "table_name": (oracle.user if target_type == "oracle" else "public") + ".target_table",
            },
        )
        transfers[f"{source_type}_{target_type}"] = transfer

    data = {
        "group_admin": MockUser(
            user=user,
            auth_token=sign_jwt(user.id, settings),
            role=TestUserRoles.Owner,
        ),
    }
    data.update(transfers)  # type: ignore
    yield data
    for transfer in transfers.values():
        await session.delete(transfer)
    await session.delete(postgres_connection)
    await session.delete(oracle_connection)
    await session.delete(hive_connection)
    await session.delete(user)
    await session.commit()
