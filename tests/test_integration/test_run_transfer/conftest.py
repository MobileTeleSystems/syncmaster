import datetime
import logging
import os
import secrets
from collections import namedtuple
from itertools import permutations
from pathlib import Path, PurePosixPath
from typing import Literal

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
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.backend.api.v1.auth.utils import sign_jwt
from syncmaster.config import Settings, TestSettings
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
    create_transfer,
    create_user,
    upload_files,
)

logger = logging.getLogger(__name__)

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


@pytest.fixture(scope="session")
def spark(settings: Settings) -> SparkSession:
    return get_spark_session(settings)


def get_spark_session(connection_settings: Settings) -> SparkSession:
    logger.info("START GET SPARK SESSION", datetime.datetime.now().isoformat())
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


@pytest.fixture
def hive(test_settings: TestSettings) -> HiveConnectionDTO:
    return HiveConnectionDTO(
        type="hive",
        cluster=test_settings.TEST_HIVE_CLUSTER,
        user=test_settings.TEST_HIVE_USER,
        password=test_settings.TEST_HIVE_PASSWORD,
    )


@pytest.fixture
def hdfs(test_settings: TestSettings) -> HDFSConnectionDTO:
    return HDFSConnectionDTO(
        type="hdfs",
        cluster=test_settings.TEST_HIVE_CLUSTER,
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


@pytest.fixture(scope="session")
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
    logger.info("START INIT DF", datetime.datetime.now().isoformat())
    df = spark.createDataFrame(data, df_schema)  # type: ignore
    logger.info("END INIT DF", datetime.datetime.now().isoformat())

    return df


@pytest.fixture
def prepare_postgres(
    spark: SparkSession,
    postgres: PostgresConnectionDTO,
    init_df: DataFrame,
) -> Postgres:
    logger.info("START PREPARE POSTGRES", datetime.datetime.now().isoformat())
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
    logger.info("END PREPARE POSTGRES", datetime.datetime.now().isoformat())
    return postgres_connection


@pytest_asyncio.fixture(
    scope="session",
)
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


@pytest_asyncio.fixture(
    scope="session",
)
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


@pytest_asyncio.fixture(scope="session")
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


@pytest_asyncio.fixture(scope="session")
def s3_file_df_connection_with_path(s3_file_connection_with_path, s3_file_df_connection):
    _, root = s3_file_connection_with_path
    return s3_file_df_connection, root


@pytest.fixture(scope="session")
def resource_path():
    path = Path(__file__).parent.parent.parent / "resources"
    assert path.exists()
    return path


@pytest.fixture(
    scope="session",
)
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


@pytest_asyncio.fixture(scope="session")
def prepare_s3(resource_path, s3_file_connection, s3_file_df_connection_with_path: tuple[SparkS3, PurePosixPath]):
    connection, upload_to = s3_file_df_connection_with_path
    files = upload_files(resource_path, upload_to, s3_file_connection)

    return connection, upload_to, files


@pytest.fixture(
    scope="session",
)
def hdfs_server():
    HDFSServer = namedtuple("HDFSServer", ["host", "webhdfs_port", "ipc_port"])
    return HDFSServer(
        host=os.getenv("HDFS_HOST"),
        webhdfs_port=os.getenv("HDFS_WEBHDFS_PORT"),
        ipc_port=os.getenv("HDFS_IPC_PORT"),
    )


@pytest.fixture(
    scope="session",
)
def hdfs_file_df_connection(spark, hdfs_server):
    from onetl.connection import SparkHDFS

    return SparkHDFS(
        cluster="test-hive",
        host=hdfs_server.host,
        ipc_port=hdfs_server.ipc_port,
        spark=spark,
    )


@pytest.fixture(
    scope="session",
)
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
    logger.info("START PREPARE HDFS", datetime.datetime.now().isoformat())
    connection, upload_to = hdfs_file_df_connection_with_path
    files = upload_files(resource_path, upload_to, hdfs_file_connection)
    logger.info("END PREPARE HDFS", datetime.datetime.now().isoformat())
    return connection, upload_to, files


@pytest.fixture
def prepare_hive(
    spark: SparkSession,
    hive: HiveConnectionDTO,
    init_df: DataFrame,
) -> Hive:
    logger.info("START PREPARE HIVE", datetime.datetime.now().isoformat())
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
    logger.info("END PREPARE HIVE", datetime.datetime.now().isoformat())
    return hive_connection


@pytest.fixture
def prepare_oracle(
    init_df: DataFrame,
    oracle: OracleConnectionDTO,
    spark: SparkSession,
) -> Oracle:
    logger.info("START PREPARE ORACLE", datetime.datetime.now().isoformat())
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
    logger.info("END PREPARE ORACLE", datetime.datetime.now().isoformat())
    return oracle_connection


@pytest_asyncio.fixture(params=["csv"])
def choice_file_format(request):
    file_format: Literal["csv", "jsonline"] = request.param
    file_format_object = None
    if file_format == "csv":
        file_format_object = CSV(
            lineSep="\n",
            header=True,
        )
    if file_format == "jsonline":
        file_format_object = JSONLine(
            encoding="utf-8",
            lineSep="\n",
        )
    if file_format == "json":
        file_format_object = JSON(
            lineSep="\n",
            encoding="utf-8",
        )
    return file_format, file_format_object


@pytest_asyncio.fixture(params=[""])
def choice_file_type(request):
    return request.param


@pytest_asyncio.fixture
async def transfers(
    choice_file_format,
    choice_file_type,
    prepare_postgres,
    prepare_oracle,
    prepare_hdfs,
    prepare_hive,
    prepare_s3,
    postgres: PostgresConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    oracle: OracleConnectionDTO,
    hive: HiveConnectionDTO,
    hdfs: HDFSConnectionDTO,
    s3: S3ConnectionDTO,
):
    logger.info("START TRANSFERS FIXTURE", datetime.datetime.now().isoformat())
    s3_file_format, file_format_object = choice_file_format
    _, source_path, _ = prepare_s3

    user = await create_user(
        session=session,
        username=f"owner_group_{secrets.token_hex(5)}",
        is_active=True,
    )
    group = await create_group(session=session, name=f"connection_group_{secrets.token_hex(5)}", owner_id=user.id)
    hive_connection = await create_connection(
        session=session,
        name=f"integration_hive_{secrets.token_hex(5)}",
        data=dict(
            type=hive.type,
            cluster=hive.cluster,
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
        name=f"integration_postgres_{secrets.token_hex(5)}",
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
        name=f"integration_oracle_{secrets.token_hex(5)}",
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

    s3_connection = await create_connection(
        session=session,
        name=f"integration_s3_{secrets.token_hex(5)}",
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
        connection_id=s3_connection.id,
        auth_data=dict(
            type="s3",
            access_key=s3.access_key,
            secret_key=s3.secret_key,
        ),
    )

    hdfs_connection = await create_connection(
        session=session,
        name=f"integration_hdfs_{secrets.token_hex(5)}",
        data=dict(
            type=hdfs.type,
            cluster=hdfs.cluster,
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=hdfs_connection.id,
        auth_data=dict(
            type="hdfs",
            user=hdfs.user,
            password=hdfs.password,
        ),
    )

    queue = await create_queue(
        session=session,
        name="test_queue",
        group_id=group.id,
    )

    transfers = {}
    for source, target in permutations(
        [
            hive_connection,
            oracle_connection,
            postgres_connection,
            s3_connection,
            hdfs_connection,
        ],
        2,
    ):
        transfer_type = ("s3", "hdfs")
        source_type = source.data["type"]
        target_type = target.data["type"]

        file_format = {}
        if (source_type in transfer_type) or (target_type in transfer_type):
            file_format = file_format_object.dict()
            file_format["type"] = s3_file_format
            file_format["timestampFormat"] = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS+00:00"

        if source_type in transfer_type:
            source_params = {
                "type": source_type,
                "directory_path": str(source_path / "file_df_connection" / s3_file_format / choice_file_type),
                "file_format": file_format,
                "df_schema": df_schema.json(),
                "options": {},
            }
        else:
            source_params = {
                "type": source_type,
                "table_name": (oracle.user if source_type == "oracle" else "public") + ".source_table",
            }

        if target_type in transfer_type:
            target_params = {
                "type": target_type,
                "directory_path": f"/target/{s3_file_format}/{choice_file_type}",
                "file_format": file_format,
                "options": {},
            }
        else:
            target_params = {
                "type": target_type,
                "table_name": (oracle.user if target_type == "oracle" else "public") + ".target_table",
            }

        transfer = await create_transfer(
            session=session,
            group_id=group.id,
            name=f"integration_transfer_{source_type}_{target_type}",
            source_connection_id=source.id,
            target_connection_id=target.id,
            source_params=source_params,
            target_params=target_params,
            queue_id=queue.id,
        )
        transfers[f"{source_type}_{target_type}"] = transfer

    data = {
        "group_owner": MockUser(
            user=user,
            auth_token=sign_jwt(user.id, settings),
            role=UserTestRoles.Owner,
        ),
    }
    data.update(transfers)  # type: ignore
    logger.info("END TRANSFERS FIXTURE", datetime.datetime.now().isoformat())
    yield data
    for transfer in transfers.values():
        await session.delete(transfer)
    await session.delete(postgres_connection)
    await session.delete(oracle_connection)
    await session.delete(hive_connection)
    await session.delete(s3_connection)
    await session.delete(hdfs_connection)
    await session.delete(user)
    await session.delete(queue)
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


@pytest.fixture
def prepare_postgres_with_mixed_column_naming(
    spark: SparkSession,
    postgres: PostgresConnectionDTO,
    init_df_with_mixed_column_naming: DataFrame,
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
    db_writer.run(init_df_with_mixed_column_naming)
    return postgres_connection


@pytest.fixture
def prepare_hive_with_mixed_column_naming(
    spark: SparkSession,
    hive: HiveConnectionDTO,
    init_df_with_mixed_column_naming: DataFrame,
) -> Hive:
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
    db_writer.run(init_df_with_mixed_column_naming)
    spark.catalog.refreshTable("public.source_table")
    return hive_connection


@pytest.fixture
def prepare_oracle_with_mixed_column_naming(
    spark: SparkSession,
    oracle: OracleConnectionDTO,
    init_df_with_mixed_column_naming: DataFrame,
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
    db_writer.run(init_df_with_mixed_column_naming)
    return oracle_connection


@pytest_asyncio.fixture
async def transfers_with_mixed_column_naming(
    prepare_postgres_with_mixed_column_naming,
    prepare_oracle_with_mixed_column_naming,
    prepare_hive_with_mixed_column_naming,
    postgres: PostgresConnectionDTO,
    oracle: OracleConnectionDTO,
    hive: HiveConnectionDTO,
    session: AsyncSession,
    settings: Settings,
):
    user = await create_user(
        session=session,
        username="owner_group",
        is_active=True,
    )
    group = await create_group(session=session, name="connection_group", owner_id=user.id)
    hive_connection = await create_connection(
        session=session,
        name="integration_hive",
        data=dict(
            type=hive.type,
            cluster=hive.cluster,
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

    queue = await create_queue(
        session=session,
        name="test_queue",
        group_id=group.id,
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
            queue_id=queue.id,
        )
        transfers[f"{source_type}_{target_type}"] = transfer

    data = {
        "group_owner": MockUser(
            user=user,
            auth_token=sign_jwt(user.id, settings),
            role=UserTestRoles.Owner,
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
    await session.delete(queue)
    await session.commit()
