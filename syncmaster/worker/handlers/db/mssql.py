# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.connection import MSSQL

from syncmaster.dto.connections import MSSQLConnectionDTO
from syncmaster.dto.transfers import MSSQLTransferDTO
from syncmaster.worker.handlers.db.base import DBHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession
    from pyspark.sql.dataframe import DataFrame


class MSSQLHandler(DBHandler):
    connection: MSSQL
    connection_dto: MSSQLConnectionDTO
    transfer_dto: MSSQLTransferDTO
    _operators = {
        "regexp": "LIKE",
        # MSSQL doesn't support traditional regexp currently
        # https://learn.microsoft.com/ru-ru/sql/t-sql/language-elements/wildcard-character-s-to-match-transact-sql?view=sql-server-ver16
        **DBHandler._operators,
    }

    def connect(self, spark: SparkSession):
        self.connection = MSSQL(
            host=self.connection_dto.host,
            port=self.connection_dto.port,
            user=self.connection_dto.user,
            password=self.connection_dto.password,
            database=self.connection_dto.database_name,
            extra={"trustServerCertificate": "true", **self.connection_dto.additional_params},
            spark=spark,
        ).check()

    def _normalize_column_names(self, df: DataFrame) -> DataFrame:
        for column_name in df.columns:
            df = df.withColumnRenamed(column_name, column_name.lower())
        return df

    def _make_rows_filter_expression(self, filters: list[dict]) -> str | None:
        expressions = []
        for filter in filters:
            op = self._operators[filter["type"]]
            field = self._quote_field(filter["field"])
            value = filter.get("value")

            if value is None:
                expressions.append(f"{field} {op}")
                continue

            if op == "ILIKE":
                expressions.append(f"LOWER({field}) LIKE LOWER('{value}')")
            elif op == "NOT ILIKE":
                expressions.append(f"NOT LOWER({field}) LIKE LOWER('{value}')")
            else:
                expressions.append(f"{field} {op} '{value}'")

        return " AND ".join(expressions) or None
