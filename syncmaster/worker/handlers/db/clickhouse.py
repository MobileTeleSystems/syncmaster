# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from onetl.connection import Clickhouse
from onetl.db import DBWriter
from onetl.hooks import slot, support_hooks

from syncmaster.worker.handlers.db.base import DBHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession
    from pyspark.sql.dataframe import DataFrame

    from syncmaster.dto.connections import ClickhouseConnectionDTO
    from syncmaster.dto.transfers import ClickhouseTransferDTO


@support_hooks
class ClickhouseHandler(DBHandler):
    connection: Clickhouse
    connection_dto: ClickhouseConnectionDTO
    transfer_dto: ClickhouseTransferDTO
    _operators: ClassVar[dict[str, str]] = {
        "regexp": "REGEXP",
        **DBHandler._operators,  # noqa: SLF001
    }

    def connect(self, spark: SparkSession):
        ClickhouseDialectRegistry = (  # noqa: N806
            spark._jvm.io.github.mtsongithub.doetl.sparkdialectextensions.clickhouse.ClickhouseDialectRegistry  # type: ignore[union-attr] # noqa: SLF001
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

    @slot
    def read(self) -> DataFrame:
        return super().read()

    @slot
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
        for filter_ in filters:
            field = self._quote_field(filter_["field"])
            op = self._operators[filter_["type"]]
            value = filter_.get("value")

            expressions.append(f"{field} {op} '{value}'" if value is not None else f"{field} {op}")

        return " AND ".join(expressions) or None
