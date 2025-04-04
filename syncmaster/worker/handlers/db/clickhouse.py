# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.connection import Clickhouse
from onetl.db import DBWriter

from syncmaster.dto.connections import ClickhouseConnectionDTO
from syncmaster.dto.transfers import ClickhouseTransferDTO
from syncmaster.worker.handlers.db.base import DBHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession
    from pyspark.sql.dataframe import DataFrame


class ClickhouseHandler(DBHandler):
    connection: Clickhouse
    connection_dto: ClickhouseConnectionDTO
    transfer_dto: ClickhouseTransferDTO
    _operators = {
        "regexp": "REGEXP",
        **DBHandler._operators,
    }

    def connect(self, spark: SparkSession):
        ClickhouseDialectRegistry = (
            spark._jvm.io.github.mtsongithub.doetl.sparkdialectextensions.clickhouse.ClickhouseDialectRegistry  # noqa: WPS219
        )
        ClickhouseDialectRegistry.register()
        self.connection = Clickhouse(
            host=self.connection_dto.host,
            port=self.connection_dto.port,
            user=self.connection_dto.user,
            password=self.connection_dto.password,
            extra=self.connection_dto.additional_params,
            spark=spark,
        ).check()

    def write(self, df: DataFrame) -> None:
        normalized_df = self._normalize_column_names(df)
        sort_column = next(
            (col for col in normalized_df.columns if col.lower().endswith("id")),
            normalized_df.columns[0],  # if there is no column with "id", take the first column
        )
        self.transfer_dto.options["createTableOptions"] = (
            f"ENGINE = MergeTree() ORDER BY {self._quote_field(sort_column)}"
        )

        if self.transfer_dto.strategy.type == "incremental" and self.hwm and self.hwm.value:
            self.transfer_dto.options["if_exists"] = "append"

        writer = DBWriter(
            connection=self.connection,
            table=self.transfer_dto.table_name,
            options=self.transfer_dto.options,
        )
        return writer.run(df=normalized_df)

    def _normalize_column_names(self, df: DataFrame) -> DataFrame:
        for column_name in df.columns:
            df = df.withColumnRenamed(column_name, column_name.lower())
        return df

    def _make_rows_filter_expression(self, filters: list[dict]) -> str | None:
        expressions = []
        for filter in filters:
            field = self._quote_field(filter["field"])
            op = self._operators[filter["type"]]
            value = filter.get("value")

            expressions.append(f"{field} {op} '{value}'" if value is not None else f"{field} {op}")

        return " AND ".join(expressions) or None
