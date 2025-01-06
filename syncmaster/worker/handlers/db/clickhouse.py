# SPDX-FileCopyrightText: 2023-2025 MTS PJSC
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

    def connect(self, spark: SparkSession):
        ClickhouseDialectRegistry = (
            spark._jvm.io.github.mtsongithub.doetl.sparkdialectextensions.clickhouse.ClickhouseDialectRegistry
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
        normalized_df = self.normalize_column_names(df)
        sort_column = next(
            (col for col in normalized_df.columns if col.lower().endswith("id")),
            normalized_df.columns[0],  # if there is no column with "id", take the first column
        )
        quoted_sort_column = f'"{sort_column}"'

        writer = DBWriter(
            connection=self.connection,
            table=self.transfer_dto.table_name,
            options=(
                Clickhouse.WriteOptions(createTableOptions=f"ENGINE = MergeTree() ORDER BY {quoted_sort_column}")
                if self.transfer_dto.type == "clickhouse"
                else None
            ),
        )
        return writer.run(df=normalized_df)

    def normalize_column_names(self, df: DataFrame) -> DataFrame:
        for column_name in df.columns:
            df = df.withColumnRenamed(column_name, column_name.lower())
        return df
