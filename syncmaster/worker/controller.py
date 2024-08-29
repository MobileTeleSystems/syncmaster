# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import logging
from typing import Any

from syncmaster.config import Settings
from syncmaster.db.models import Connection, Run
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
from syncmaster.worker.handlers.db.hive import HiveHandler
from syncmaster.worker.handlers.db.oracle import OracleHandler
from syncmaster.worker.handlers.db.postgres import PostgresHandler
from syncmaster.worker.handlers.file.hdfs import HDFSHandler
from syncmaster.worker.handlers.file.s3 import S3Handler

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
        run: Run,
        source_connection: Connection,
        source_auth_data: dict,
        target_connection: Connection,
        target_auth_data: dict,
        settings: Settings,
    ):
        self.run = run
        self.settings = settings
        self.source_handler = self.get_handler(
            connection_data=source_connection.data,
            transfer_params=run.transfer.source_params,
            connection_auth_data=source_auth_data,
        )
        self.target_handler = self.get_handler(
            connection_data=target_connection.data,
            transfer_params=run.transfer.target_params,
            connection_auth_data=target_auth_data,
        )

    def perform_transfer(self) -> None:
        spark = self.settings.CREATE_SPARK_SESSION_FUNCTION(
            settings=self.settings,
            run=self.run,
            source=self.source_handler.connection_dto,
            target=self.target_handler.connection_dto,
        )

        with spark:
            self.source_handler.connect(spark)
            self.target_handler.connect(spark)

            df = self.source_handler.read()
            self.target_handler.write(df)

    def get_handler(
        self,
        connection_data: dict[str, Any],
        connection_auth_data: dict,
        transfer_params: dict[str, Any],
    ) -> Handler:
        connection_data.update(connection_auth_data)
        handler_type = connection_data.pop("type")
        transfer_params.pop("type", None)

        if connection_handler_proxy.get(handler_type, None) is None:
            raise ConnectionTypeNotRecognizedError

        handler, connection_dto, transfer_dto = connection_handler_proxy[handler_type]

        return handler(
            connection_dto=connection_dto(**connection_data),
            transfer_dto=transfer_dto(**transfer_params),
        )
