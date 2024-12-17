import datetime
import logging
import os
import secrets
from collections import namedtuple
from pathlib import Path, PosixPath, PurePosixPath

import pyspark
import pytest
import pytest_asyncio
from onetl.connection import MSSQL, Clickhouse, Hive, MySQL, Oracle, Postgres, SparkS3
from onetl.connection.file_connection.s3 import S3
from onetl.db import DBWriter
from onetl.file.format import CSV, JSON, ORC, XML, Excel, JSONLine, Parquet
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

from syncmaster.backend.settings import ServerAppSettings as Settings
from syncmaster.db.models import Group
from syncmaster.dto.connections import (
    ClickhouseConnectionDTO,
    HDFSConnectionDTO,
    HiveConnectionDTO,
    MSSQLConnectionDTO,
    MySQLConnectionDTO,
    OracleConnectionDTO,
    PostgresConnectionDTO,
    S3ConnectionDTO,
)
from tests.mocks import MockUser, UserTestRoles
from tests.resources.file_df_connection.test_data import data
from tests.settings import TestSettings
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
def spark(settings: Settings, request: FixtureRequest) -> SparkSession:
    logger.info("START GET SPARK SESSION")

    # get markers from all downstream tests
    markers = set()
    for func in request.session.items:
        markers.update(marker.name for marker in func.iter_markers())

    maven_packages: list[str] = []
    excluded_packages: list[str] = []

    spark = (
        SparkSession.builder.appName("celery_worker")
        .enableHiveSupport()
        .config("spark.sql.pyspark.jvmStacktrace.enabled", "true")
        .config("spark.driver.host", "localhost")
    )

    if "postgres" in markers:
        maven_packages.extend(Postgres.get_packages())

    if "oracle" in markers:
        maven_packages.extend(Oracle.get_packages())

    if "clickhouse" in markers:
        maven_packages.append("io.github.mtsongithub.doetl:spark-dialect-extension_2.12:0.0.2")
        maven_packages.extend(Clickhouse.get_packages())

    if "mssql" in markers:
        maven_packages.extend(MSSQL.get_packages())

    if "mysql" in markers:
        maven_packages.extend(MySQL.get_packages())

    if "s3" in markers:
        maven_packages.extend(SparkS3.get_packages(spark_version=pyspark.__version__))
        excluded_packages.extend(
            [
                "com.google.cloud.bigdataoss:gcs-connector",
                "org.apache.hadoop:hadoop-aliyun",
                "org.apache.hadoop:hadoop-azure-datalake",
                "org.apache.hadoop:hadoop-azure",
            ],
        )
        spark = (
            spark.config("spark.hadoop.fs.s3a.committer.magic.enabled", "true")
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

    if "hdfs" in markers or "s3" in markers:
        # excel version is hardcoded due to https://github.com/nightscape/spark-excel/issues/902
        file_formats_spark_packages: list[str] = XML.get_packages(
            spark_version=pyspark.__version__,
        ) + Excel.get_packages(spark_version="3.5.1")
        maven_packages.extend(file_formats_spark_packages)

    if maven_packages:
        spark = spark.config("spark.jars.packages", ",".join(maven_packages))

    if excluded_packages:
        spark = spark.config("spark.jars.excludes", ",".join(excluded_packages))

    return spark.getOrCreate()


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


@pytest.fixture(
    scope="session",
    params=[pytest.param("hdfs", marks=[pytest.mark.hdfs])],
)
def hdfs(test_settings: TestSettings) -> HDFSConnectionDTO:
    return HDFSConnectionDTO(
        cluster=test_settings.TEST_HIVE_CLUSTER,
        user=test_settings.TEST_HIVE_USER,
        password=test_settings.TEST_HIVE_PASSWORD,
    )


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
        additional_params={},
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
        additional_params={},
    )


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
        additional_params={},
    )


@pytest.fixture(
    scope="session",
    params=[pytest.param("mssql", marks=[pytest.mark.mssql])],
)
def mssql_for_worker(test_settings: TestSettings) -> MSSQLConnectionDTO:
    return MSSQLConnectionDTO(
        host=test_settings.TEST_MSSQL_HOST_FOR_CONFTEST,
        port=test_settings.TEST_MSSQL_PORT_FOR_CONFTEST,
        user=test_settings.TEST_MSSQL_USER,
        password=test_settings.TEST_MSSQL_PASSWORD,
        database_name=test_settings.TEST_MSSQL_DB,
        additional_params={},
    )


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
        additional_params={},
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
        additional_params={},
    )


@pytest.fixture(
    scope="session",
    params=[pytest.param("s3", marks=[pytest.mark.s3])],
)
def s3_for_conftest(test_settings: TestSettings) -> S3ConnectionDTO:
    return S3ConnectionDTO(
        host=test_settings.TEST_S3_HOST_FOR_CONFTEST,
        port=test_settings.TEST_S3_PORT_FOR_CONFTEST,
        bucket=test_settings.TEST_S3_BUCKET,
        access_key=test_settings.TEST_S3_ACCESS_KEY,
        secret_key=test_settings.TEST_S3_SECRET_KEY,
        protocol=test_settings.TEST_S3_PROTOCOL,
        additional_params=test_settings.TEST_S3_ADDITIONAL_PARAMS,
    )


@pytest.fixture(
    scope="session",
    params=[pytest.param("s3", marks=[pytest.mark.s3])],
)
def s3_for_worker(test_settings: TestSettings) -> S3ConnectionDTO:
    return S3ConnectionDTO(
        host=test_settings.TEST_S3_HOST_FOR_WORKER,
        port=test_settings.TEST_S3_PORT_FOR_WORKER,
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


@pytest.fixture(scope="session")
def s3_server(s3_for_conftest):
    S3Server = namedtuple("S3Server", ["host", "port", "bucket", "access_key", "secret_key", "protocol"])

    return S3Server(
        host=s3_for_conftest.host,
        port=s3_for_conftest.port,
        bucket=s3_for_conftest.bucket,
        access_key=s3_for_conftest.access_key,
        secret_key=s3_for_conftest.secret_key,
        protocol=s3_for_conftest.protocol,
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
def prepare_s3(
    resource_path: PosixPath,
    s3_file_connection: S3,
    s3_file_df_connection_with_path: tuple[SparkS3, PurePosixPath],
):
    logger.info("START PREPARE S3")
    connection, remote_path = s3_file_df_connection_with_path

    s3_file_connection.remove_dir(remote_path, recursive=True)
    files = upload_files(resource_path, remote_path, s3_file_connection)

    yield connection, remote_path, files

    logger.info("START POST-CLEANUP S3")
    s3_file_connection.remove_dir(remote_path, recursive=True)
    logger.info("END POST-CLEANUP S3")


@pytest.fixture(scope="session")
def hdfs_server():
    HDFSServer = namedtuple("HDFSServer", ["host", "webhdfs_port", "ipc_port"])
    return HDFSServer(
        host=os.getenv("TEST_HDFS_HOST"),
        webhdfs_port=os.getenv("TEST_HDFS_WEBHDFS_PORT"),
        ipc_port=os.getenv("TEST_HDFS_IPC_PORT"),
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


@pytest.fixture()
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

    if name == "excel":
        return "excel", Excel(
            header=True,
            inferSchema=True,
            **params,
        )

    if name == "orc":
        return "orc", ORC(
            **params,
        )

    if name == "parquet":
        return "parquet", Parquet(
            **params,
        )

    if name == "xml":
        return "xml", XML(
            row_tag="item",
            **params,
        )

    raise ValueError(f"Unsupported file format: {name}")


@pytest.fixture()
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

    if name == "excel":
        return "excel", Excel(
            header=False,
            **params,
        )

    if name == "orc":
        return "orc", ORC(
            **params,
        )

    if name == "parquet":
        return "parquet", Parquet(
            **params,
        )

    if name == "xml":
        return "xml", XML(
            row_tag="item",
            **params,
        )

    raise ValueError(f"Unsupported file format: {name}")


@pytest_asyncio.fixture
async def group_owner(
    settings: Settings,
    session: AsyncSession,
    access_token_factory,
):
    user = await create_user(
        session=session,
        username=secrets.token_hex(5),
        is_active=True,
    )

    token = access_token_factory(user.id)
    yield MockUser(
        user=user,
        auth_token=token,
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
        slug=request.param,
    )
    yield result
    await session.delete(result)
    await session.commit()


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
            user=postgres.user,
            password=postgres.password,
        ),
    )

    yield syncmaster_conn
    await session.delete(syncmaster_conn)
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
            user=clickhouse.user,
            password=clickhouse.password,
        ),
    )

    yield syncmaster_conn
    await session.delete(syncmaster_conn)
    await session.commit()


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
            user=mssql.user,
            password=mssql.password,
        ),
    )

    yield syncmaster_conn
    await session.delete(syncmaster_conn)
    await session.commit()


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
        type=hdfs.type,
        data=dict(
            cluster=hdfs.cluster,
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=result.id,
        auth_data=dict(
            type="basic",
            user=hdfs.user,
            password=hdfs.password,
        ),
    )

    yield result
    await session.delete(result)
    await session.commit()


@pytest_asyncio.fixture
async def s3_connection(
    s3_for_worker: S3ConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    group: Group,
):
    s3 = s3_for_worker
    syncmaster_conn = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        type=s3.type,
        data=dict(
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
        connection_id=syncmaster_conn.id,
        auth_data=dict(
            type="s3",
            access_key=s3.access_key,
            secret_key=s3.secret_key,
        ),
    )

    yield syncmaster_conn
    await session.delete(syncmaster_conn)
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
