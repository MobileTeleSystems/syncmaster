# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

HIVE_TYPE = Literal["hive"]
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
    "oracle",
    "postgres",
    "clickhouse",
    "hive",
    "mssql",
    "mysql",
    "s3",
    "hdfs",
    "sftp",
    "ftp",
    "ftps",
    "webdav",
    "samba",
]
FILE_CONNECTION_TYPES = ["s3", "hdfs", "sftp", "ftp", "ftps", "webdav", "samba"]
DB_CONNECTION_TYPES = ["oracle", "postgres", "clickhouse", "hive", "mssql", "mysql"]
