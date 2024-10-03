# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from enum import Enum
from typing import Literal

HIVE_TYPE = Literal["hive"]
ORACLE_TYPE = Literal["oracle"]
POSTGRES_TYPE = Literal["postgres"]
S3_TYPE = Literal["s3"]
HDFS_TYPE = Literal["hdfs"]


class ConnectionType(str, Enum):
    HIVE = "hive"
    ORACLE = "oracle"
    POSTGRES = "postgres"
    S3 = "s3"
    HDFS = "hdfs"
