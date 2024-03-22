# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from abc import ABC

from onetl.db import DBReader, DBWriter
from pyspark.sql import SparkSession
from pyspark.sql.dataframe import DataFrame

from syncmaster.dto.connections import ConnectionDTO
from syncmaster.dto.transfers import TransferDTO


class Handler(ABC):
    def __init__(
        self,
        connection_dto: ConnectionDTO,
        transfer_dto: TransferDTO,
        spark: SparkSession | None = None,
    ) -> None:
        self.spark = spark
        self.reader: DBReader | None = None
        self.writer: DBWriter | None = None
        self.connection_dto = connection_dto
        self.transfer_dto = transfer_dto

    def init_connection(self): ...

    def set_spark(self, spark: SparkSession):
        self.spark = spark

    def init_reader(self):
        if self.connection_dto is None:
            raise ValueError("At first you need to initialize connection. Run `init_connection")

    def init_writer(self):
        if self.connection_dto is None:
            raise ValueError("At first you need to initialize connection. Run `init_connection")

    def read(self) -> DataFrame:
        if self.reader is None:
            raise ValueError("Reader is not initialized")
        return self.reader.run()

    def write(self, df: DataFrame) -> None:
        if self.writer is None:
            raise ValueError("Writer is not initialized")
        return self.writer.run(df=df)

    def normalize_column_name(self, df: DataFrame) -> DataFrame: ...
