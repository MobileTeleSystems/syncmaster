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
        reader = DBReader(
            connection=self.connection,
            table=self.transfer_dto.table_name,
            where=self._get_rows_filter_expression(),
            columns=self._get_columns_filter_expressions(),
        )
        return reader.run()

    def write(self, df: DataFrame) -> None:
        writer = DBWriter(
            connection=self.connection,
            table=self.transfer_dto.table_name,
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

        if expressions:
            return self._make_rows_filter_expression(expressions)

        return None

    def _get_columns_filter_expressions(self) -> list[str] | None:
        expressions = []
        for transformation in self.transfer_dto.transformations:
            if transformation["type"] == "dataframe_columns_filter":
                expressions.extend(transformation["filters"])

        if expressions:
            return self._make_columns_filter_expressions(expressions)

        return None

    @staticmethod
    def _quote_field(field: str) -> str:
        return f'"{field}"'
