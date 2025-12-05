# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

# Using a dedicated module to avoid importing other SyncMaster modules,
# for better docker caching
from onetl.connection import (
    MSSQL,
    Clickhouse,
    Iceberg,
    MySQL,
    Oracle,
    Postgres,
    SparkS3,
)
from onetl.file.format import XML, Excel


def get_packages(connection_types: set[str]) -> list[str]:  # noqa: WPS212
    import pyspark

    spark_version = pyspark.__version__
    # excel version is hardcoded due to https://github.com/nightscape/spark-excel/issues/902
    file_formats_spark_packages: list[str] = [
        *XML.get_packages(spark_version=spark_version),
        *Excel.get_packages(package_version="0.31.2", spark_version="3.5.6"),
    ]

    result = []
    if connection_types & {"postgres", "all"}:
        result.extend(Postgres.get_packages())
    if connection_types & {"oracle", "all"}:
        result.extend(Oracle.get_packages())
    if connection_types & {"clickhouse", "all"}:
        result.append("io.github.mtsongithub.doetl:spark-dialect-extension_2.12:0.0.2")
        result.extend(Clickhouse.get_packages())
    if connection_types & {"mssql", "all"}:
        result.extend(MSSQL.get_packages())
    if connection_types & {"mysql", "all"}:
        result.extend(MySQL.get_packages())

    if connection_types & {"s3", "all"}:
        result.extend(SparkS3.get_packages(spark_version=spark_version))

    if connection_types & {"iceberg", "all"}:
        result.extend(
            [
                *Iceberg.get_packages(package_version="1.10.0", spark_version=spark_version),
                *Iceberg.S3Warehouse.get_packages(package_version="1.10.0"),
            ],
        )

    if connection_types & {"s3", "hdfs", "sftp", "ftp", "ftps", "samba", "webdav", "all"}:
        result.extend(file_formats_spark_packages)

    return result


def get_excluded_packages() -> list[str]:
    return SparkS3.get_exclude_packages()
