# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from onetl.base import BaseDBConnection
from onetl.db import DBReader, DBWriter

from syncmaster.dto.transfers import DBTransferDTO
from syncmaster.worker.handlers.base import Handler

if TYPE_CHECKING:
    from pyspark.sql.dataframe import DataFrame


class DBHandler(Handler):
    connection: BaseDBConnection
    transfer_dto: DBTransferDTO

    _operators = {
        "is_null": "IS NULL",
        "is_not_null": "IS NOT NULL",
        "equal": "=",
        "not_equal": "!=",
        "greater_than": ">",
        "greater_or_equal": ">=",
        "less_than": "<",
        "less_or_equal": "<=",
        "like": "LIKE",
        "ilike": "ILIKE",
        "not_like": "NOT LIKE",
        "not_ilike": "NOT ILIKE",
    }

    def read(self) -> DataFrame:
        reader_params = {}
        if self.transfer_dto.strategy.type == "incremental":
            self.transfer_dto.strategy.increment_by = self._quote_field(self.transfer_dto.strategy.increment_by)
            hwm_name = (
                f"{self.transfer_dto.id}_{self.connection_dto.type}_{self.transfer_dto.table_name}"  # noqa: WPS237
            )
            reader_params["hwm"] = DBReader.AutoDetectHWM(
                name=hwm_name,
                expression=self.transfer_dto.strategy.increment_by,
            )

        reader_params.update(self._get_reading_options())

        reader = DBReader(
            connection=self.connection,
            table=self.transfer_dto.table_name,
            where=self._get_rows_filter_expression(),
            columns=self._get_columns_filter_expressions(),
            **reader_params,
        )
        return reader.run()

    def write(self, df: DataFrame) -> None:
        if self.transfer_dto.strategy.type == "incremental" and self.hwm and self.hwm.value:
            self.transfer_dto.options["if_exists"] = "append"

        writer = DBWriter(
            connection=self.connection,
            table=self.transfer_dto.table_name,
            options=self.transfer_dto.options,
        )
        return writer.run(df=self._normalize_column_names(df))

    @abstractmethod
    def _normalize_column_names(self, df: DataFrame) -> DataFrame: ...

    @abstractmethod
    def _make_rows_filter_expression(self, filters: list[dict]) -> str | None: ...

    def _make_columns_filter_expressions(self, filters: list[dict]) -> list[str] | None:
        expressions = []
        for filter in filters:
            filter_type = filter["type"]
            field = self._quote_field(filter["field"])

            if filter_type == "include":
                expressions.append(field)
            elif filter_type == "rename":
                new_name = self._quote_field(filter["to"])
                expressions.append(f"{field} AS {new_name}")
            elif filter_type == "cast":
                cast_type = filter["as_type"]
                expressions.append(f"CAST({field} AS {cast_type}) AS {field}")

        return expressions or None

    def _get_rows_filter_expression(self) -> str | None:
        expressions = []
        for transformation in self.transfer_dto.transformations:
            if transformation["type"] == "dataframe_rows_filter":
                expressions.extend(transformation["filters"])

        return self._make_rows_filter_expression(expressions)

    def _get_columns_filter_expressions(self) -> list[str] | None:
        expressions = []
        for transformation in self.transfer_dto.transformations:
            if transformation["type"] == "dataframe_columns_filter":
                expressions.extend(transformation["filters"])

        return self._make_columns_filter_expressions(expressions)

    def _get_reading_options(self) -> dict:
        options = {}

        if self.transfer_dto.resources.max_parallel_tasks < 2:
            return options

        if self.transfer_dto.strategy.type == "incremental":
            # using "range" partitioning if HWM is available for efficient min/max lookup,
            # since the incremental column is usually an indexed primary key
            options["options"] = {
                "partition_column": self.transfer_dto.strategy.increment_by,
                "num_partitions": self.transfer_dto.resources.max_parallel_tasks,
                "partitioning_mode": "range" if self.hwm and self.hwm.value else "hash",
            }

        elif self.transfer_dto.strategy.type == "full":
            schema = self.connection.get_df_schema(
                source=self.transfer_dto.table_name,
                columns=self._get_columns_filter_expressions(),
            )
            # using "hash" partitioning as it works with any column type and improves full scan performance
            options["options"] = {
                "partition_column": self._quote_field(schema[0].name),
                "num_partitions": self.transfer_dto.resources.max_parallel_tasks,
                "partitioning_mode": "hash",
            }

        return options

    def _quote_field(self, field: str) -> str:
        return f'"{field}"'
