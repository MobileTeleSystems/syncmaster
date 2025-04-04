# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.connection import Hive

from syncmaster.dto.connections import HiveConnectionDTO
from syncmaster.dto.transfers import HiveTransferDTO
from syncmaster.worker.handlers.db.base import DBHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession
    from pyspark.sql.dataframe import DataFrame


class HiveHandler(DBHandler):
    connection: Hive
    connection_dto: HiveConnectionDTO
    transfer_dto: HiveTransferDTO
    _operators = {
        "regexp": "RLIKE",
        **DBHandler._operators,
    }

    def connect(self, spark: SparkSession):
        self.connection = Hive(
            cluster=self.connection_dto.cluster,
            spark=spark,
        ).check()

    def read(self) -> DataFrame:
        self.connection.spark.catalog.refreshTable(self.transfer_dto.table_name)
        return super().read()

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

    def _get_reading_options(self) -> dict:
        return {}

    def _quote_field(self, field: str) -> str:
        return f"`{field}`"
