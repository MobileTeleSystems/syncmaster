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

        filter_expression = self._get_filter_expression()
        if filter_expression:
            df = df.where(filter_expression)

        return df

    def write(self, df: DataFrame):
        writer = FileDFWriter(
            connection=self.connection,
            format=self.transfer_dto.file_format,
            target_path=self.transfer_dto.directory_path,
            options=self.transfer_dto.options,
        )

        return writer.run(df=df)

    def _get_filter_expression(self) -> str | None:
        filters = []
        for transformation in self.transfer_dto.transformations:
            if transformation["type"] == "dataframe_rows_filter":
                filters.extend(transformation["filters"])
        if filters:
            return self._make_filter_expression(filters)
        return None

    def _make_filter_expression(self, filters: list[dict]) -> str:
        expressions = []
        for filter in filters:
            field = filter["field"]
            op = self._operators[filter["type"]]
            value = filter.get("value")

            expressions.append(f"{field} {op} '{value}'" if value is not None else f"{field} {op}")

        return " AND ".join(expressions)
