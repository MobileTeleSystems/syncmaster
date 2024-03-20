# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from onetl.connection import Oracle
from onetl.db import DBReader, DBWriter
from pyspark.sql.dataframe import DataFrame

from syncmaster.dto.connections import OracleConnectionDTO
from syncmaster.dto.transfers import OracleTransferDTO
from syncmaster.worker.handlers.base import Handler


class OracleHandler(Handler):
    connection: Oracle
    connection_dto: OracleConnectionDTO
    transfer_dto: OracleTransferDTO

    def init_connection(self):
        self.connection = Oracle(
            host=self.connection_dto.host,
            port=self.connection_dto.port,
            user=self.connection_dto.user,
            password=self.connection_dto.password,
            sid=self.connection_dto.sid,
            service_name=self.connection_dto.service_name,
            extra=self.connection_dto.additional_params,
            spark=self.spark,
        ).check()

    def init_reader(self):
        super().init_reader()
        df = self.connection.get_df_schema(self.transfer_dto.table_name)
        self.reader = DBReader(
            connection=self.connection,
            table=self.transfer_dto.table_name,
            columns=[f'"{f}"' for f in df.fieldNames()],
        )

    def init_writer(self):
        super().init_writer()
        self.writer = DBWriter(
            connection=self.connection,
            table=self.transfer_dto.table_name,
        )

    def normalize_column_name(self, df: DataFrame) -> DataFrame:
        for column_name in df.columns:
            df = df.withColumnRenamed(column_name, column_name.upper())
        return df
