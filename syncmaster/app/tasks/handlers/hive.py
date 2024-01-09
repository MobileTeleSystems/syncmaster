# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from onetl.connection import Hive
from onetl.db import DBReader, DBWriter
from pyspark.sql.dataframe import DataFrame

from app.dto.connections import HiveConnectionDTO
from app.dto.transfers import HiveTransferParamsDTO
from app.tasks.handlers.base import Handler


class HiveHandler(Handler):
    connection: Hive
    connection_dto: HiveConnectionDTO
    transfer_params: HiveTransferParamsDTO

    def init_connection(self):
        self.connection = Hive(
            cluster=self.connection_dto.cluster,
            spark=self.spark,
        ).check()

    def init_reader(self):
        super().init_reader()
        self.spark.catalog.refreshTable(self.transfer_params.table_name)
        self.reader = DBReader(
            connection=self.connection,
            table=self.transfer_params.table_name,
        )

    def init_writer(self):
        super().init_writer()
        self.writer = DBWriter(
            connection=self.connection,
            table=self.transfer_params.table_name,
        )

    def normalize_column_name(self, df: DataFrame) -> DataFrame:
        for column_name in df.columns:
            df = df.withColumnRenamed(column_name, column_name.lower())
        return df
