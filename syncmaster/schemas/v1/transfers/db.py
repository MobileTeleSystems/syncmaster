# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import re
from typing import ClassVar

from pydantic import BaseModel, Field, field_validator

from syncmaster.schemas.v1.connection_types import (
    CLICKHOUSE_TYPE,
    HIVE_TYPE,
    ICEBERG_TYPE,
    MSSQL_TYPE,
    MYSQL_TYPE,
    ORACLE_TYPE,
    POSTGRES_TYPE,
)


class DBTransfer(BaseModel):
    TABLE_NAME_PATTERN: ClassVar[str] = r"^[\w\d]+\.[\w\d]+$"
    table_name: str = Field(description="Table name", json_schema_extra={"pattern": TABLE_NAME_PATTERN})

    # make error message more user friendly
    @field_validator("table_name", mode="before")
    @classmethod
    def _table_name_is_qualified(cls, value):
        if not re.match(cls.TABLE_NAME_PATTERN, value):
            msg = "Table name should be in format myschema.mytable"
            raise ValueError(msg)
        return value


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


class IcebergTransferSourceOrTarget(DBTransfer):
    type: ICEBERG_TYPE

    TABLE_NAME_PATTERN: ClassVar[str] = r"^[\w\d]+(\.[\w\d]+)+$"
    table_name: str = Field(description="Table name", json_schema_extra={"pattern": TABLE_NAME_PATTERN})

    # make error message more user friendly
    @field_validator("table_name", mode="before")
    @classmethod
    def _table_name_is_qualified(cls, value):
        if not re.match(cls.TABLE_NAME_PATTERN, value):
            msg = "Table name should be in format myschema.mytable"
            raise ValueError(msg)
        return value


DBTransferSourceOrTarget = (
    ClickhouseTransferSourceOrTarget
    | HiveTransferSourceOrTarget
    | IcebergTransferSourceOrTarget
    | MSSQLTransferSourceOrTarget
    | MySQLTransferSourceOrTarget
    | OracleTransferSourceOrTarget
    | PostgresTransferSourceOrTarget
)

__all__ = [
    "DBTransferSourceOrTarget",
]
