# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
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

    def connect(self, spark: SparkSession):
        self.connection = Hive(
            cluster=self.connection_dto.cluster,
            spark=spark,
        ).check()

    def read(self) -> DataFrame:
        self.connection.spark.catalog.refreshTable(self.transfer_dto.table_name)
        return super().read()

    def normalize_column_names(self, df: DataFrame) -> DataFrame:
        for column_name in df.columns:
            df = df.withColumnRenamed(column_name, column_name.lower())
        return df
