# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from onetl.connection import Postgres
from onetl.hooks import slot, support_hooks

from syncmaster.worker.handlers.db.base import DBHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession
    from pyspark.sql.dataframe import DataFrame

    from syncmaster.dto.connections import PostgresConnectionDTO
    from syncmaster.dto.transfers import PostgresTransferDTO


@support_hooks
class PostgresHandler(DBHandler):
    connection: Postgres
    connection_dto: PostgresConnectionDTO
    transfer_dto: PostgresTransferDTO
    _operators: ClassVar[dict[str, str]] = {
        "regexp": "~",
        **DBHandler._operators,  # noqa: SLF001
    }

    def connect(self, spark: SparkSession):
        self.connection = Postgres(
            host=self.connection_dto.host,
            user=self.connection_dto.user,
            password=self.connection_dto.password,
            port=self.connection_dto.port,
            database=self.connection_dto.database_name,
            extra=self.connection_dto.additional_params,
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
            field = self._quote_field(filter_["field"])
            op = self._operators[filter_["type"]]
            value = filter_.get("value")

            expressions.append(f"{field} {op} '{value}'" if value is not None else f"{field} {op}")

        return " AND ".join(expressions) or None
