# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

HIVE_TYPE = Literal["hive"]
ICEBERG_REST_S3_TYPE = Literal["iceberg_rest_s3"]
ORACLE_TYPE = Literal["oracle"]
POSTGRES_TYPE = Literal["postgres"]
CLICKHOUSE_TYPE = Literal["clickhouse"]
MSSQL_TYPE = Literal["mssql"]
MYSQL_TYPE = Literal["mysql"]
S3_TYPE = Literal["s3"]
HDFS_TYPE = Literal["hdfs"]
SFTP_TYPE = Literal["sftp"]
FTP_TYPE = Literal["ftp"]
FTPS_TYPE = Literal["ftps"]
WEBDAV_TYPE = Literal["webdav"]
SAMBA_TYPE = Literal["samba"]

CONNECTION_TYPES = [
    "clickhouse",
    "hive",
    "iceberg_rest_s3",
    "mssql",
    "mysql",
    "oracle",
    "postgres",
    "ftp",
    "ftps",
    "hdfs",
    "s3",
    "samba",
    "sftp",
    "webdav",
]
FILE_CONNECTION_TYPES = [
    "ftp",
    "ftps",
    "hdfs",
    "s3",
    "samba",
    "sftp",
    "webdav",
]
DB_CONNECTION_TYPES = [
    "clickhouse",
    "hive",
    "iceberg_rest_s3",
    "mssql",
    "mysql",
    "oracle",
    "postgres",
]
CONNECTION_TYPES = [*DB_CONNECTION_TYPES, *FILE_CONNECTION_TYPES]
