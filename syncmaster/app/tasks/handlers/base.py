from abc import ABC

from onetl.db import DBReader, DBWriter
from pyspark.sql import SparkSession
from pyspark.sql.dataframe import DataFrame

from app.dto.connections import OracleConnectionDTO, PostgresConnectionDTO
from app.dto.transfers import OracleTransferParamsDTO, PostgresTransferParamsDTO


class Handler(ABC):
    def __init__(
        self,
        connection: PostgresConnectionDTO | OracleConnectionDTO,
        transfer_params: OracleTransferParamsDTO | PostgresTransferParamsDTO,
        spark: SparkSession,
    ) -> None:
        self.spark = spark
        self.reader: DBReader | None = None
        self.writer: DBWriter | None = None
        self.connection_dto = connection
        self.transfer_params = transfer_params

    def init_connection(self):
        pass

    def init_reader(self):
        if self.connection_dto is None:
            raise ValueError(
                "At first you need to initialize connection. " "Run `init_connection"
            )

    def init_writer(self):
        if self.connection_dto is None:
            raise ValueError(
                "At first you need to initialize connection. " "Run `init_connection"
            )

    def read(self) -> DataFrame:
        if self.reader is None:
            raise ValueError("Reader is not initialized")
        return self.reader.run()

    def write(self, df: DataFrame) -> None:
        if self.writer is None:
            raise ValueError("Writer is not initialized")
        return self.writer.run(df=df)
