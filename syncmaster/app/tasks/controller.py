import logging
from typing import Any

from app.config import Settings
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
from app.exceptions import ConnectionTypeNotRecognizedError
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
        source_auth_data: dict,
        target_connection: Connection,
        target_auth_data: dict,
        settings: Settings,
    ):
        self.source = self.get_handler(
            connection_data=source_connection.data,
            transfer_params=transfer.source_params,
            connection_auth_data=source_auth_data,
        )
        self.target = self.get_handler(
            connection_data=target_connection.data,
            transfer_params=transfer.target_params,
            connection_auth_data=target_auth_data,
        )
        spark = settings.CREATE_SPARK_SESSION_FUNCTION(
            settings,
            target=self.target.connection_dto,
            source=self.source.connection_dto,
        )
        self.source.set_spark(spark)
        self.target.set_spark(spark)
        logger.info("source connection = %s", self.source)
        logger.info("target connection = %s", self.target)

    def make_transfer(self) -> None:
        self.source.init_connection()
        self.source.init_reader()

        self.target.init_connection()
        self.target.init_writer()
        logger.info("Source and target were initialized")

        df = self.target.normalize_column_name(self.source.read())
        logger.info("Data has been read")

        self.target.write(df)
        logger.info("Data has been inserted")

    def get_handler(
        self,
        connection_data: dict[str, Any],
        connection_auth_data: dict,
        transfer_params: dict[str, Any],
    ) -> Handler:
        connection_data.update(connection_auth_data)
        if connection_data.get("type") == "hive":
            return HiveHandler(
                connection=HiveConnectionDTO(**connection_data),
                transfer_params=HiveTransferParamsDTO(**transfer_params),
            )

        if connection_data.get("type") == "oracle":
            return OracleHandler(
                connection=OracleConnectionDTO(**connection_data),
                transfer_params=OracleTransferParamsDTO(**transfer_params),
            )
        if connection_data.get("type") == "postgres":
            return PostgresHandler(
                connection=PostgresConnectionDTO(**connection_data),
                transfer_params=PostgresTransferParamsDTO(**transfer_params),
            )
        raise ConnectionTypeNotRecognizedError
