from typing import Any

from pyspark.sql import SparkSession

from app.api.v1.schemas import ORACLE_TYPE, POSTGRES_TYPE
from app.celery.handlers.base import Handler
from app.celery.handlers.oracle import OracleHandler
from app.celery.handlers.postgres import PostgresHandler
from app.db.models import Connection, Transfer
from app.dto.connections import OracleConnectionDTO, PostgresConnectionDTO
from app.dto.transfers import OracleTransferParamsDTO, PostgresTransferParamsDTO
from app.exceptions import ConnectionTypeNotRecognizedException


class TransferController:
    source: Handler
    target: Handler

    def __init__(
        self,
        transfer: Transfer,
        source_connection: Connection,
        target_connection: Connection,
        spark: SparkSession,
    ):
        self.source = self.get_handler(
            source_connection.data, transfer.source_params, spark
        )
        self.target = self.get_handler(
            target_connection.data, transfer.target_params, spark
        )

    def make_transfer(self) -> None:
        self.source.init_connection()
        self.source.init_reader()

        self.target.init_connection()
        self.target.init_writer()

        df = self.source.read()
        self.target.write(df)

    def get_handler(
        self,
        connection_data: dict[str, Any],
        transfer_params: dict[str, Any],
        spark: SparkSession,
    ) -> Handler:
        if connection_data.get("type") == ORACLE_TYPE:
            return OracleHandler(
                connection=OracleConnectionDTO(**connection_data),
                transfer_params=OracleTransferParamsDTO(**transfer_params),
                spark=spark,
            )
        if connection_data.get("type") == POSTGRES_TYPE:
            return PostgresHandler(
                connection=PostgresConnectionDTO(**connection_data),
                transfer_params=PostgresTransferParamsDTO(**transfer_params),
                spark=spark,
            )
        raise ConnectionTypeNotRecognizedException
