# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.base.base_file_df_connection import BaseFileDFConnection
from onetl.file import FileDFReader, FileDFWriter

from syncmaster.dto.connections import ConnectionDTO
from syncmaster.dto.transfers import FileTransferDTO
from syncmaster.worker.handlers.base import Handler

if TYPE_CHECKING:
    from pyspark.sql.dataframe import DataFrame


class FileHandler(Handler):
    connection: BaseFileDFConnection
    connection_dto: ConnectionDTO
    transfer_dto: FileTransferDTO
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
        "regexp": "RLIKE",
    }

    def read(self) -> DataFrame:
        from pyspark.sql.types import StructType

        reader = FileDFReader(
            connection=self.connection,
            format=self.transfer_dto.file_format,
            source_path=self.transfer_dto.directory_path,
            df_schema=StructType.fromJson(self.transfer_dto.df_schema) if self.transfer_dto.df_schema else None,
            options=self.transfer_dto.options,
        )
        df = reader.run()

        rows_filter_expression = self._get_rows_filter_expression()
        if rows_filter_expression:
            df = df.where(rows_filter_expression)

        columns_filter_expressions = self._get_columns_filter_expressions()
        if columns_filter_expressions:
            df = df.selectExpr(*columns_filter_expressions)

        return df

    def write(self, df: DataFrame) -> None:
        writer = FileDFWriter(
            connection=self.connection,
            format=self.transfer_dto.file_format,
            target_path=self.transfer_dto.directory_path,
            options=self.transfer_dto.options,
        )

        return writer.run(df=df)

    def _make_rows_filter_expression(self, filters: list[dict]) -> str | None:
        expressions = []
        for filter in filters:
            field = filter["field"]
            op = self._operators[filter["type"]]
            value = filter.get("value")

            expressions.append(f"{field} {op} '{value}'" if value is not None else f"{field} {op}")

        return " AND ".join(expressions) or None

    def _make_columns_filter_expressions(self, filters: list[dict]) -> list[str] | None:
        # TODO: another approach is to use df.select(col("col1"), col("col2").alias("new_col2"), ...)
        expressions = []
        for filter in filters:
            filter_type = filter["type"]
            field = filter["field"]

            if filter_type == "include":
                expressions.append(field)
            elif filter_type == "rename":
                new_name = filter["to"]
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
