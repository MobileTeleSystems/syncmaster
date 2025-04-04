# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pydantic import BaseModel

from syncmaster.schemas.v1.connection_types import (
    CLICKHOUSE_TYPE,
    HIVE_TYPE,
    MSSQL_TYPE,
    MYSQL_TYPE,
    ORACLE_TYPE,
    POSTGRES_TYPE,
)


class ReadDBTransfer(BaseModel):
    table_name: str


class HiveReadTransferSourceAndTarget(ReadDBTransfer):
    type: HIVE_TYPE


class OracleReadTransferSourceAndTarget(ReadDBTransfer):
    type: ORACLE_TYPE


class PostgresReadTransferSourceAndTarget(ReadDBTransfer):
    type: POSTGRES_TYPE


class ClickhouseReadTransferSourceAndTarget(ReadDBTransfer):
    type: CLICKHOUSE_TYPE


class MSSQLReadTransferSourceAndTarget(ReadDBTransfer):
    type: MSSQL_TYPE


class MySQLReadTransferSourceAndTarget(ReadDBTransfer):
    type: MYSQL_TYPE
