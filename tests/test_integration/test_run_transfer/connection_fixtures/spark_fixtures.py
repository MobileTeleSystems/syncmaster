import logging

import pyspark
import pytest
from onetl.connection import MSSQL, Clickhouse, MySQL, Oracle, Postgres, SparkS3
from onetl.file.format import XML, Excel
from pyspark.sql import SparkSession
from pytest import FixtureRequest

from syncmaster.server.settings import ServerAppSettings as Settings

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
        .config("spark.hadoop.mapreduce.fileoutputcommitter.marksuccessfuljobs", "false")
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

    if set(markers).intersection({"hdfs", "s3", "sftp", "ftp", "ftps"}):
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
