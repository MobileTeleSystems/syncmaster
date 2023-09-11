from pyspark.sql import SparkSession

from app.api.v1.connections.schemas import (
    ReadOracleConnectionData,
    ReadPostgresConnectionData,
)
from app.api.v1.schemas import ORACLE_TYPE, POSTGRES_TYPE
from app.api.v1.transfers.schemas import (
    ReadFullTransferSchema,
    ReadOracleTransferData,
    ReadPostgresTransferData,
)
from app.celery.handlers.base import Handler
from app.celery.handlers.oracle import OracleHandler
from app.celery.handlers.postgres import PostgresHandler
from app.exceptions import ConnectionTypeNotRecognizedException


class TransferController:
    source: Handler
    target: Handler

    def __init__(self, transfer_data, spark: SparkSession):
        transfer = ReadFullTransferSchema(transfer_data)
        transfer.source_connection.data
        self.source = self.get_handler(
            transfer.source_connection.data, transfer.source_params, spark
        )
        self.target = self.get_handler(
            transfer.target_connection.data, transfer.target_params, spark
        )

    def make_transfer(self) -> None:
        self.source.init_connection()
        self.source.init_reader()

        self.target.init_connection()
        self.target.init_writer()

        df = self.source.read()
        self.target.write(df)

    def get_handler(
        connection_data: ReadPostgresConnectionData | ReadOracleConnectionData,
        transfer_params: ReadOracleTransferData | ReadPostgresTransferData,
        spark: SparkSession,
    ) -> Handler:
        if connection_data.type == ORACLE_TYPE:
            return OracleHandler(
                connection=connection_data,
                transfer_params=transfer_params,
                spark=spark,
            )
        if connection_data.type == POSTGRES_TYPE:
            return PostgresHandler(
                connection=connection_data,
                transfer_params=transfer_params,
                spark=spark,
            )
        raise ConnectionTypeNotRecognizedException
