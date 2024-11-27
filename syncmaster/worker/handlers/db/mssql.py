# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.connection import MSSQL

from syncmaster.dto.connections import MSSQLConnectionDTO
from syncmaster.dto.transfers import MSSQLTransferDTO
from syncmaster.worker.handlers.db.base import DBHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession
    from pyspark.sql.dataframe import DataFrame


class MSSQLHandler(DBHandler):
    connection: MSSQL
    connection_dto: MSSQLConnectionDTO
    transfer_dto: MSSQLTransferDTO

    def connect(self, spark: SparkSession):
        self.connection = MSSQL(
            host=self.connection_dto.host,
            port=self.connection_dto.port,
            user=self.connection_dto.user,
            password=self.connection_dto.password,
            database=self.connection_dto.database_name,
            extra=self.connection_dto.additional_params or {"trustServerCertificate": "true"},
            spark=spark,
        ).check()

    def normalize_column_names(self, df: DataFrame) -> DataFrame:
        for column_name in df.columns:
            df = df.withColumnRenamed(column_name, column_name.lower())
        return df
