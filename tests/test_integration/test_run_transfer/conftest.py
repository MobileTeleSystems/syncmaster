import datetime
import logging
import os
import secrets
from collections import namedtuple
from pathlib import Path, PurePosixPath

import pytest
import pytest_asyncio
from onetl.connection import Hive, Oracle, Postgres, SparkS3
from onetl.db import DBWriter
from onetl.file.format import CSV, JSON, JSONLine
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
from pytest import FixtureRequest
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.backend.api.v1.auth.utils import sign_jwt
from syncmaster.config import Settings, TestSettings
from syncmaster.db.models import Group
from syncmaster.dto.connections import (
    HDFSConnectionDTO,
    HiveConnectionDTO,
    OracleConnectionDTO,
    PostgresConnectionDTO,
    S3ConnectionDTO,
)
from tests.mocks import MockUser, UserTestRoles
from tests.resources.file_df_connection.test_data import data
from tests.test_unit.utils import (
    create_connection,
    create_credentials,
    create_group,
    create_queue,
    create_user,
    upload_files,
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def spark(settings: Settings) -> SparkSession:
    return get_spark_session(settings)


def get_spark_session(connection_settings: Settings) -> SparkSession:
    logger.info("START GET SPARK SESSION")
    maven_packages = [p for connection in (Postgres, Oracle) for p in connection.get_packages()]
    maven_s3_packages = [p for p in SparkS3.get_packages(spark_version="3.4.1")]
    maven_packages.extend(maven_s3_packages)

    spark = (
        SparkSession.builder.appName("celery_worker")
        .config("spark.jars.packages", ",".join(maven_packages))
        .config("spark.sql.pyspark.jvmStacktrace.enabled", "true")
        .enableHiveSupport()
    )

    excluded_packages = [
        "com.google.cloud.bigdataoss:gcs-connector",
        "org.apache.hadoop:hadoop-aliyun",
        "org.apache.hadoop:hadoop-azure-datalake",
        "org.apache.hadoop:hadoop-azure",
    ]
    spark = (
        spark.config("spark.jars.excludes", ",".join(excluded_packages))
        .config("spark.hadoop.fs.s3a.committer.magic.enabled", "true")
        .config("spark.hadoop.fs.s3a.committer.name", "magic")
        .config(
            "spark.hadoop.mapreduce.outputcommitter.factory.scheme.s3a",
            "org.apache.hadoop.fs.s3a.commit.S3ACommitterFactory",
        )
        .config(
            "spark.sql.parquet.output.committer.class",
            "org.apache.spark.internal.io.cloud.BindingParquetOutputCommitter",
        )
        .config(
            "spark.sql.sources.commitProtocolClass",
            "org.apache.spark.internal.io.cloud.PathOutputCommitProtocol",
        )
    )

    return spark.getOrCreate()


@pytest.fixture(
    scope="session",
    params=[pytest.param("hive", marks=[pytest.mark.hive])],
)
def hive(test_settings: TestSettings) -> HiveConnectionDTO:
    return HiveConnectionDTO(
        type="hive",
        cluster=test_settings.TEST_HIVE_CLUSTER,
        user=test_settings.TEST_HIVE_USER,
        password=test_settings.TEST_HIVE_PASSWORD,
    )


@pytest.fixture(
    scope="session",
    params=[pytest.param("hdfs", marks=[pytest.mark.hdfs])],
)
def hdfs(test_settings: TestSettings) -> HDFSConnectionDTO:
    return HDFSConnectionDTO(
        type="hdfs",
        cluster=test_settings.TEST_HIVE_CLUSTER,
        user=test_settings.TEST_HIVE_USER,
        password=test_settings.TEST_HIVE_PASSWORD,
    )


@pytest.fixture(
    scope="session",
    params=[pytest.param("oracle", marks=[pytest.mark.oracle])],
)
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


@pytest.fixture(
    scope="session",
    params=[pytest.param("postgres", marks=[pytest.mark.postgres])],
)
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


@pytest.fixture(
    scope="session",
    params=[pytest.param("s3", marks=[pytest.mark.s3])],
)
def s3(test_settings: TestSettings) -> S3ConnectionDTO:
    return S3ConnectionDTO(
        type="s3",
        host=test_settings.TEST_S3_HOST,
        port=test_settings.TEST_S3_PORT,
        bucket=test_settings.TEST_S3_BUCKET,
        access_key=test_settings.TEST_S3_ACCESS_KEY,
        secret_key=test_settings.TEST_S3_SECRET_KEY,
        protocol=test_settings.TEST_S3_PROTOCOL,
        additional_params=test_settings.TEST_S3_ADDITIONAL_PARAMS,
    )


@pytest.fixture
def init_df(spark: SparkSession) -> DataFrame:
    logger.info("START INIT DF")
    df_schema = StructType(
        [
            StructField("ID", IntegerType()),
            StructField("PHONE_NUMBER", StringType()),
            StructField("REGION", StringType()),
            StructField("NUMBER", IntegerType()),
            StructField("BIRTH_DATE", DateType()),
            StructField("REGISTERED_AT", TimestampType()),
            StructField("ACCOUNT_BALANCE", DoubleType()),
        ],
    )
    df = spark.createDataFrame(data, schema=df_schema)
    logger.info("END INIT DF")
    return df


@pytest.fixture
def prepare_postgres(
    spark: SparkSession,
    postgres: PostgresConnectionDTO,
):
    result = Postgres(
        host=postgres.host,
        port=postgres.port,
        user=postgres.user,
        password=postgres.password,
        database=postgres.database_name,
        spark=spark,
    ).check()
    result.execute("DROP TABLE IF EXISTS public.source_table")
    result.execute("DROP TABLE IF EXISTS public.target_table")

    def fill_with_data(df: DataFrame):
        logger.info("START PREPARE POSTGRES")
        db_writer = DBWriter(
            connection=result,
            target="public.source_table",
            options=Postgres.WriteOptions(if_exists="append"),
        )
        db_writer.run(df)
        logger.info("END PREPARE POSTGRES")

    yield result, fill_with_data
    result.execute("DROP TABLE IF EXISTS public.source_table")
    result.execute("DROP TABLE IF EXISTS public.target_table")


@pytest.fixture(scope="session")
def s3_server(s3):
    S3Server = namedtuple("S3Server", ["host", "port", "bucket", "access_key", "secret_key", "protocol"])

    return S3Server(
        host=s3.host,
        port=s3.port,
        bucket=s3.bucket,
        access_key=s3.access_key,
        secret_key=s3.secret_key,
        protocol=s3.protocol,
    )


@pytest.fixture(scope="session")
def s3_file_connection(s3_server):
    from onetl.connection import S3

    s3_connection = S3(
        host=s3_server.host,
        port=s3_server.port,
        bucket=s3_server.bucket,
        access_key=s3_server.access_key,
        secret_key=s3_server.secret_key,
        protocol=s3_server.protocol,
    )

    if not s3_connection.client.bucket_exists(s3_server.bucket):
        s3_connection.client.make_bucket(s3_server.bucket)

    return s3_connection


@pytest.fixture(scope="session")
def s3_file_connection_with_path(request, s3_file_connection):
    connection = s3_file_connection
    source = PurePosixPath("/data")
    target = PurePosixPath("/target")

    def finalizer():
        connection.remove_dir(source, recursive=True)
        connection.remove_dir(target, recursive=True)

    request.addfinalizer(finalizer)
    connection.remove_dir(source, recursive=True)
    connection.remove_dir(target, recursive=True)

    return connection, source


@pytest.fixture(scope="session")
def s3_file_df_connection_with_path(s3_file_connection_with_path, s3_file_df_connection):
    _, root = s3_file_connection_with_path
    return s3_file_df_connection, root


@pytest.fixture(scope="session")
def resource_path():
    path = Path(__file__).parent.parent.parent / "resources"
    assert path.exists()
    return path


@pytest.fixture(scope="session")
def s3_file_df_connection(s3_file_connection, spark, s3_server):
    from onetl.connection import SparkS3

    return SparkS3(
        host=s3_server.host,
        port=s3_server.port,
        bucket=s3_server.bucket,
        access_key=s3_server.access_key,
        secret_key=s3_server.secret_key,
        protocol=s3_server.protocol,
        extra={
            "path.style.access": True,
        },
        spark=spark,
    )


@pytest.fixture(scope="session")
def prepare_s3(resource_path, s3_file_connection, s3_file_df_connection_with_path: tuple[SparkS3, PurePosixPath]):
    logger.info("START PREPARE HDFS")
    connection, upload_to = s3_file_df_connection_with_path
    files = upload_files(resource_path, upload_to, s3_file_connection)
    logger.info("END PREPARE HDFS")
    return connection, upload_to, files


@pytest.fixture(scope="session")
def hdfs_server():
    HDFSServer = namedtuple("HDFSServer", ["host", "webhdfs_port", "ipc_port"])
    return HDFSServer(
        host=os.getenv("HDFS_HOST"),
        webhdfs_port=os.getenv("HDFS_WEBHDFS_PORT"),
        ipc_port=os.getenv("HDFS_IPC_PORT"),
    )


@pytest.fixture(scope="session")
def hdfs_file_df_connection(spark, hdfs_server):
    from onetl.connection import SparkHDFS

    return SparkHDFS(
        cluster="test-hive",
        host=hdfs_server.host,
        ipc_port=hdfs_server.ipc_port,
        spark=spark,
    )


@pytest.fixture(scope="session")
def hdfs_file_connection(hdfs_server):
    from onetl.connection import HDFS

    return HDFS(host=hdfs_server.host, webhdfs_port=hdfs_server.webhdfs_port)


@pytest.fixture()
def hdfs_file_connection_with_path(request, hdfs_file_connection):
    connection = hdfs_file_connection
    source = PurePosixPath("/data")
    target = PurePosixPath("/target")

    def finalizer():
        connection.remove_dir(source, recursive=True)
        connection.remove_dir(target, recursive=True)

    request.addfinalizer(finalizer)

    connection.remove_dir(source, recursive=True)
    connection.remove_dir(target, recursive=True)
    connection.create_dir(source)

    return connection, source


@pytest.fixture()
def hdfs_file_df_connection_with_path(hdfs_file_connection_with_path, hdfs_file_df_connection):
    _, source = hdfs_file_connection_with_path
    return hdfs_file_df_connection, source


@pytest.fixture()
def prepare_hdfs(
    hdfs_file_df_connection_with_path,
    hdfs_file_connection,
    resource_path,
):
    logger.info("START PREPARE HDFS")
    connection, upload_to = hdfs_file_df_connection_with_path
    files = upload_files(resource_path, upload_to, hdfs_file_connection)
    logger.info("END PREPARE HDFS")
    return connection, upload_to, files


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


@pytest.fixture
def prepare_oracle(
    oracle: OracleConnectionDTO,
    spark: SparkSession,
):
    result = Oracle(
        host=oracle.host,
        port=oracle.port,
        user=oracle.user,
        password=oracle.password,
        sid=oracle.sid,
        service_name=oracle.service_name,
        spark=spark,
    ).check()
    try:
        result.execute(f"DROP TABLE {oracle.user}.source_table")
    except Exception:
        pass
    try:
        result.execute(f"DROP TABLE {oracle.user}.target_table")
    except Exception:
        pass

    def fill_with_data(df: DataFrame):
        logger.info("START PREPARE ORACLE")
        db_writer = DBWriter(
            connection=result,
            target=f"{oracle.user}.source_table",
            options=Oracle.WriteOptions(if_exists="append"),
        )
        db_writer.run(df)
        logger.info("END PREPARE ORACLE")

    yield result, fill_with_data

    try:
        result.execute(f"DROP TABLE {oracle.user}.source_table")
    except Exception:
        pass
    try:
        result.execute(f"DROP TABLE {oracle.user}.target_table")
    except Exception:
        pass


@pytest.fixture(params=[("csv", {}), ("jsonline", {}), ("json", {})])
def source_file_format(request: FixtureRequest):
    name, params = request.param
    if name == "csv":
        return "csv", CSV(
            lineSep="\n",
            header=True,
            **params,
        )

    if name == "jsonline":
        return "jsonline", JSONLine(
            encoding="utf-8",
            lineSep="\n",
            **params,
        )

    if name == "json":
        return "json", JSON(
            lineSep="\n",
            encoding="utf-8",
            **params,
        )

    raise ValueError(f"Unsupported file format: {name}")


@pytest.fixture(params=[("csv", {}), ("jsonline", {})])
def target_file_format(request: FixtureRequest):
    name, params = request.param
    if name == "csv":
        return "csv", CSV(
            lineSep="\n",
            header=True,
            timestampFormat="yyyy-MM-dd'T'HH:mm:ss.SSSSSS+00:00",
            **params,
        )

    if name == "jsonline":
        return "jsonline", JSONLine(
            encoding="utf-8",
            lineSep="\n",
            timestampFormat="yyyy-MM-dd'T'HH:mm:ss.SSSSSS+00:00",
            **params,
        )

    raise ValueError(f"Unsupported file format: {name}")


@pytest_asyncio.fixture
async def group_owner(
    settings: Settings,
    session: AsyncSession,
):
    user = await create_user(
        session=session,
        username=secrets.token_hex(5),
        is_active=True,
    )

    yield MockUser(
        user=user,
        auth_token=sign_jwt(user.id, settings),
        role=UserTestRoles.Owner,
    )

    await session.delete(user)
    await session.commit()


@pytest_asyncio.fixture
async def group(
    session: AsyncSession,
    group_owner: MockUser,
):
    result = await create_group(session=session, name=secrets.token_hex(5), owner_id=group_owner.user.id)
    yield result
    await session.delete(result)
    await session.commit()


@pytest_asyncio.fixture(params=["test_queue"])
async def queue(
    request: FixtureRequest,
    session: AsyncSession,
    group: Group,
):
    result = await create_queue(
        session=session,
        name=request.param,
        group_id=group.id,
    )
    yield result
    await session.delete(result)
    await session.commit()


@pytest_asyncio.fixture
async def postgres_connection(
    postgres: PostgresConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    group: Group,
):
    result = await create_connection(
        session=session,
        name=secrets.token_hex(5),
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
        connection_id=result.id,
        auth_data=dict(
            type="postgres",
            user=postgres.user,
            password=postgres.password,
        ),
    )

    yield result
    await session.delete(result)
    await session.commit()


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
        data=dict(
            type=hive.type,
            cluster=hive.cluster,
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=result.id,
        auth_data=dict(
            type="hive",
            user=hive.user,
            password=hive.password,
        ),
    )

    yield result
    await session.delete(result)
    await session.commit()


@pytest_asyncio.fixture
async def oracle_connection(
    oracle: OracleConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    group: Group,
):
    result = await create_connection(
        session=session,
        name=secrets.token_hex(5),
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
        connection_id=result.id,
        auth_data=dict(
            type="oracle",
            user=oracle.user,
            password=oracle.password,
        ),
    )

    yield result
    await session.delete(result)
    await session.commit()


@pytest_asyncio.fixture
async def hdfs_connection(
    hdfs: HDFSConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    group: Group,
):
    result = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        data=dict(
            type=hdfs.type,
            cluster=hdfs.cluster,
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=result.id,
        auth_data=dict(
            type="hdfs",
            user=hdfs.user,
            password=hdfs.password,
        ),
    )

    yield result
    await session.delete(result)
    await session.commit()


@pytest_asyncio.fixture
async def s3_connection(
    s3: S3ConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    group: Group,
):
    result = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        data=dict(
            type=s3.type,
            host=s3.host,
            port=s3.port,
            bucket=s3.bucket,
            protocol=s3.protocol,
            additional_params={
                "path.style.access": True,
            },
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=result.id,
        auth_data=dict(
            type="s3",
            access_key=s3.access_key,
            secret_key=s3.secret_key,
        ),
    )

    yield result
    await session.delete(result)
    await session.commit()


@pytest.fixture
def init_df_with_mixed_column_naming(spark: SparkSession) -> DataFrame:
    df_schema = StructType(
        [
            StructField("Id", IntegerType()),
            StructField("Phone Number", StringType()),
            StructField("region", StringType()),
            StructField("birth_DATE", DateType()),
            StructField("Registered At", TimestampType()),
            StructField("account_balance", DoubleType()),
        ],
    )

    return spark.createDataFrame(
        data=[
            (
                1,
                "+79123456789",
                "Mordor",
                datetime.date(year=2023, month=3, day=11),
                datetime.datetime.now(),
                1234.2343,
            ),
        ],
        schema=df_schema,
    )
