# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.connection import Oracle

from syncmaster.dto.connections import OracleConnectionDTO
from syncmaster.dto.transfers import OracleTransferDTO
from syncmaster.worker.handlers.db.base import DBHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession
    from pyspark.sql.dataframe import DataFrame


class OracleHandler(DBHandler):
    connection: Oracle
    connection_dto: OracleConnectionDTO
    transfer_dto: OracleTransferDTO
    _operators = {
        "regexp": "REGEXP_LIKE",
        **DBHandler._operators,
    }

    def connect(self, spark: SparkSession):
        self.connection = Oracle(
            host=self.connection_dto.host,
            port=self.connection_dto.port,
            user=self.connection_dto.user,
            password=self.connection_dto.password,
            sid=self.connection_dto.sid,
            service_name=self.connection_dto.service_name,
            extra=self.connection_dto.additional_params,
            spark=spark,
        ).check()

    def _normalize_column_names(self, df: DataFrame) -> DataFrame:
        for column_name in df.columns:
            df = df.withColumnRenamed(column_name, column_name.upper())
        return df

    def _make_rows_filter_expression(self, filters: list[dict]) -> str | None:
        expressions = []
        for filter in filters:
            field = self._quote_field(filter["field"])
            op = self._operators[filter["type"]]
            value = filter.get("value")

            if value is None:
                expressions.append(f"{field} {op}")
                continue

            if op == "REGEXP_LIKE":
                expressions.append(f"REGEXP_LIKE({field}, '{value}')")
            elif op == "ILIKE":
                expressions.append(f"LOWER({field}) LIKE LOWER('{value}')")
            elif op == "NOT ILIKE":
                expressions.append(f"NOT LOWER({field}) LIKE LOWER('{value}')")
            else:
                expressions.append(f"{field} {op} '{value}'")

        return " AND ".join(expressions) or None
