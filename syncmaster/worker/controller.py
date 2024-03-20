# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
import logging
from typing import Any

from syncmaster.config import Settings
from syncmaster.db.models import Connection, Transfer
from syncmaster.dto.connections import (
    HDFSConnectionDTO,
    HiveConnectionDTO,
    OracleConnectionDTO,
    PostgresConnectionDTO,
    S3ConnectionDTO,
)
from syncmaster.dto.transfers import (
    HDFSTransferDTO,
    HiveTransferDTO,
    OracleTransferDTO,
    PostgresTransferDTO,
    S3TransferDTO,
)
from syncmaster.exceptions.connection import ConnectionTypeNotRecognizedError
from syncmaster.worker.handlers.base import Handler
from syncmaster.worker.handlers.file.hdfs import HDFSHandler
from syncmaster.worker.handlers.file.s3 import S3Handler
from syncmaster.worker.handlers.hive import HiveHandler
from syncmaster.worker.handlers.oracle import OracleHandler
from syncmaster.worker.handlers.postgres import PostgresHandler

logger = logging.getLogger(__name__)


connection_handler_proxy = {
    "hive": (
        HiveHandler,
        HiveConnectionDTO,
        HiveTransferDTO,
    ),
    "oracle": (
        OracleHandler,
        OracleConnectionDTO,
        OracleTransferDTO,
    ),
    "postgres": (
        PostgresHandler,
        PostgresConnectionDTO,
        PostgresTransferDTO,
    ),
    "s3": (
        S3Handler,
        S3ConnectionDTO,
        S3TransferDTO,
    ),
    "hdfs": (
        HDFSHandler,
        HDFSConnectionDTO,
        HDFSTransferDTO,
    ),
}


class TransferController:
    source_handler: Handler
    target_handler: Handler

    def __init__(
        self,
        transfer: Transfer,
        source_connection: Connection,
        source_auth_data: dict,
        target_connection: Connection,
        target_auth_data: dict,
        settings: Settings,
    ):
        self.source_handler = self.get_handler(
            connection_data=source_connection.data,
            transfer_params=transfer.source_params,
            connection_auth_data=source_auth_data,
        )
        self.target_handler = self.get_handler(
            connection_data=target_connection.data,
            transfer_params=transfer.target_params,
            connection_auth_data=target_auth_data,
        )
        spark = settings.CREATE_SPARK_SESSION_FUNCTION(
            settings,
            target=self.target_handler.connection_dto,
            source=self.source_handler.connection_dto,
        )

        self.source_handler.set_spark(spark)
        self.target_handler.set_spark(spark)
        logger.info("source connection = %s", self.source_handler)
        logger.info("target connection = %s", self.target_handler)

    def start_transfer(self) -> None:
        self.source_handler.init_connection()
        self.source_handler.init_reader()

        self.target_handler.init_connection()
        self.target_handler.init_writer()
        logger.info("Source and target were initialized")

        df = self.target_handler.normalize_column_name(self.source_handler.read())
        logger.info("Data has been read")

        self.target_handler.write(df)
        logger.info("Data has been inserted")

    def get_handler(
        self,
        connection_data: dict[str, Any],
        connection_auth_data: dict,
        transfer_params: dict[str, Any],
    ) -> Handler:
        connection_data.update(connection_auth_data)
        handler_type = connection_data["type"]

        if connection_handler_proxy.get(handler_type, None) is None:
            raise ConnectionTypeNotRecognizedError

        handler, connection_dto, transfer_dto = connection_handler_proxy[handler_type]

        return handler(
            connection_dto=connection_dto(**connection_data),
            transfer_dto=transfer_dto(**transfer_params),
        )
