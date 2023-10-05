import logging
from typing import Any

from pyspark.sql import SparkSession

from app.db.models import Connection, Transfer
from app.dto.connections import (
    HiveConnectionDTO,
    OracleConnectionDTO,
    PostgresConnectionDTO,
)
from app.dto.transfers import (
    HiveTransferParamsDTO,
    OracleTransferParamsDTO,
    PostgresTransferParamsDTO,
)
from app.exceptions import ConnectionTypeNotRecognizedException
from app.tasks.handlers.base import Handler
from app.tasks.handlers.hive import HiveHandler
from app.tasks.handlers.oracle import OracleHandler
from app.tasks.handlers.postgres import PostgresHandler

logger = logging.getLogger(__name__)


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
            source_connection.data,
            source_connection.auth_data,
            transfer.source_params,
            spark,
        )
        self.target = self.get_handler(
            target_connection.data,
            target_connection.auth_data,
            transfer.target_params,
            spark,
        )
        logger.info("source connection = %s", self.source)
        logger.info("target connection = %s", self.target)

    def make_transfer(self) -> None:
        self.source.init_connection()
        self.source.init_reader()

        self.target.init_connection()
        self.target.init_writer()
        logger.info("Source and target were initialized")
        df = self.source.read()
        self.target.write(df)

    def get_handler(
        self,
        connection_data: dict[str, Any],
        connection_auth_data: dict[str, Any],
        transfer_params: dict[str, Any],
        spark: SparkSession,
    ) -> Handler:
        connection_data.update(connection_auth_data)
        if connection_data.get("type") == "hive":
            return HiveHandler(
                connection=HiveConnectionDTO(**connection_data),
                transfer_params=HiveTransferParamsDTO(**transfer_params),
                spark=spark,
            )

        if connection_data.get("type") == "oracle":
            return OracleHandler(
                connection=OracleConnectionDTO(**connection_data),
                transfer_params=OracleTransferParamsDTO(**transfer_params),
                spark=spark,
            )
        if connection_data.get("type") == "postgres":
            return PostgresHandler(
                connection=PostgresConnectionDTO(**connection_data),
                transfer_params=PostgresTransferParamsDTO(**transfer_params),
                spark=spark,
            )
        raise ConnectionTypeNotRecognizedException
