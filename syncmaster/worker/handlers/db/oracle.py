# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.connection import Oracle

from syncmaster.dto.connections import OracleConnectionDTO
from syncmaster.dto.transfers import OracleTransferDTO
from syncmaster.worker.handlers.db.base import DBHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession
    from pyspark.sql.dataframe import DataFrame


class OracleHandler(DBHandler):
    connection: Oracle
    connection_dto: OracleConnectionDTO
    transfer_dto: OracleTransferDTO

    def connect(self, spark: SparkSession):
        self.connection = Oracle(
            host=self.connection_dto.host,
            port=self.connection_dto.port,
            user=self.connection_dto.user,
            password=self.connection_dto.password,
            sid=self.connection_dto.sid,
            service_name=self.connection_dto.service_name,
            extra=self.connection_dto.additional_params,
            spark=spark,
        ).check()

    def normalize_column_names(self, df: DataFrame) -> DataFrame:
        for column_name in df.columns:
            df = df.withColumnRenamed(column_name, column_name.upper())
        return df
