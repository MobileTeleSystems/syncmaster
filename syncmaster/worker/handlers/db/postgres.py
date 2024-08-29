# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.connection import Postgres

from syncmaster.dto.connections import PostgresConnectionDTO
from syncmaster.dto.transfers import PostgresTransferDTO
from syncmaster.worker.handlers.db.base import DBHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession
    from pyspark.sql.dataframe import DataFrame


class PostgresHandler(DBHandler):
    connection: Postgres
    connection_dto: PostgresConnectionDTO
    transfer_dto: PostgresTransferDTO

    def connect(self, spark: SparkSession):
        self.connection = Postgres(
            host=self.connection_dto.host,
            user=self.connection_dto.user,
            password=self.connection_dto.password,
            port=self.connection_dto.port,
            database=self.connection_dto.database_name,
            extra=self.connection_dto.additional_params,
            spark=spark,
        ).check()

    def normalize_column_names(self, df: DataFrame) -> DataFrame:
        for column_name in df.columns:
            df = df.withColumnRenamed(column_name, column_name.lower())
        return df
