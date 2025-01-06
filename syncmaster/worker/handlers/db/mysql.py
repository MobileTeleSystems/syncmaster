# SPDX-FileCopyrightText: 2023-2025 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.connection import MySQL

from syncmaster.dto.connections import MySQLConnectionDTO
from syncmaster.dto.transfers import MySQLTransferDTO
from syncmaster.worker.handlers.db.base import DBHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession
    from pyspark.sql.dataframe import DataFrame


class MySQLHandler(DBHandler):
    connection: MySQL
    connection_dto: MySQLConnectionDTO
    transfer_dto: MySQLTransferDTO

    def connect(self, spark: SparkSession):
        self.connection = MySQL(
            host=self.connection_dto.host,
            port=self.connection_dto.port,
            user=self.connection_dto.user,
            password=self.connection_dto.password,
            database=self.connection_dto.database_name,
            spark=spark,
        ).check()

    def normalize_column_names(self, df: DataFrame) -> DataFrame:
        for column_name in df.columns:
            df = df.withColumnRenamed(column_name, column_name.lower())
        return df
