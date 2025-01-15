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
            where=self._get_filter_expression(),
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
    def _make_filter_expression(self, filters: list[dict]) -> str | None: ...

    def _get_filter_expression(self) -> str | None:
        filters = []
        for transformation in self.transfer_dto.transformations:
            if transformation["type"] == "dataframe_rows_filter":
                filters.extend(transformation["filters"])
        if filters:
            return self._make_filter_expression(filters)
        return None
