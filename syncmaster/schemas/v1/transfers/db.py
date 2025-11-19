# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pydantic import BaseModel

from syncmaster.schemas.v1.connection_types import (
    CLICKHOUSE_TYPE,
    HIVE_TYPE,
    ICEBERG_REST_S3_TYPE,
    MSSQL_TYPE,
    MYSQL_TYPE,
    ORACLE_TYPE,
    POSTGRES_TYPE,
)


class DBTransfer(BaseModel):
    table_name: str


class HiveTransferSourceOrTarget(DBTransfer):
    type: HIVE_TYPE


class OracleTransferSourceOrTarget(DBTransfer):
    type: ORACLE_TYPE


class PostgresTransferSourceOrTarget(DBTransfer):
    type: POSTGRES_TYPE


class ClickhouseTransferSourceOrTarget(DBTransfer):
    type: CLICKHOUSE_TYPE


class MSSQLTransferSourceOrTarget(DBTransfer):
    type: MSSQL_TYPE


class MySQLTransferSourceOrTarget(DBTransfer):
    type: MYSQL_TYPE


class IcebergRESTCatalogS3TransferSourceOrTarget(DBTransfer):
    type: ICEBERG_REST_S3_TYPE
