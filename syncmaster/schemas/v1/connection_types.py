# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from enum import Enum
from typing import Literal

HIVE_TYPE = Literal["hive"]
ORACLE_TYPE = Literal["oracle"]
POSTGRES_TYPE = Literal["postgres"]
CLICKHOUSE_TYPE = Literal["clickhouse"]
MSSQL_TYPE = Literal["mssql"]
MYSQL_TYPE = Literal["mysql"]
S3_TYPE = Literal["s3"]
HDFS_TYPE = Literal["hdfs"]


class ConnectionType(str, Enum):
    POSTGRES = "postgres"
    HIVE = "hive"
    ORACLE = "oracle"
    CLICKHOUSE = "clickhouse"
    MSSQL = "mssql"
    MYSQL = "mysql"
    S3 = "s3"
    HDFS = "hdfs"
