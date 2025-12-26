# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from onetl.connection import MSSQL
from onetl.hooks import slot, support_hooks

from syncmaster.worker.handlers.db.base import DBHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession
    from pyspark.sql.dataframe import DataFrame

    from syncmaster.dto.connections import MSSQLConnectionDTO
    from syncmaster.dto.transfers import MSSQLTransferDTO


@support_hooks
class MSSQLHandler(DBHandler):
    connection: MSSQL
    connection_dto: MSSQLConnectionDTO
    transfer_dto: MSSQLTransferDTO
    _operators: ClassVar[dict[str, str]] = {
        "regexp": "LIKE",
        # MSSQL doesn't support traditional regexp currently
        # https://learn.microsoft.com/ru-ru/sql/t-sql/language-elements/wildcard-character-s-to-match-transact-sql?view=sql-server-ver16
        **DBHandler._operators,  # noqa: SLF001
    }

    def connect(self, spark: SparkSession):
        self.connection = MSSQL(
            host=self.connection_dto.host,
            port=self.connection_dto.port,
            user=self.connection_dto.user,
            password=self.connection_dto.password,
            database=self.connection_dto.database_name,
            extra={
                "trustServerCertificate": "true",
                **self.connection_dto.additional_params,
            },
            spark=spark,
        ).check()

    @slot
    def read(self) -> DataFrame:
        return super().read()

    @slot
    def write(self, df: DataFrame) -> None:
        return super().write(df)

    def _normalize_column_names(self, df: DataFrame) -> DataFrame:
        for column_name in df.columns:
            df = df.withColumnRenamed(column_name, column_name.lower())
        return df

    def _make_rows_filter_expression(self, filters: list[dict]) -> str | None:
        expressions = []
        for filter_ in filters:
            op = self._operators[filter_["type"]]
            field = self._quote_field(filter_["field"])
            value = filter_.get("value")

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
