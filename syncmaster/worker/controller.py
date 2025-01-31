# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import logging
from tempfile import TemporaryDirectory
from typing import Any

from syncmaster.db.models import Connection, Run
from syncmaster.dto.connections import (
    ClickhouseConnectionDTO,
    FTPConnectionDTO,
    FTPSConnectionDTO,
    HDFSConnectionDTO,
    HiveConnectionDTO,
    MSSQLConnectionDTO,
    MySQLConnectionDTO,
    OracleConnectionDTO,
    PostgresConnectionDTO,
    S3ConnectionDTO,
    SFTPConnectionDTO,
)
from syncmaster.dto.transfers import (
    ClickhouseTransferDTO,
    FTPSTransferDTO,
    FTPTransferDTO,
    HDFSTransferDTO,
    HiveTransferDTO,
    MSSQLTransferDTO,
    MySQLTransferDTO,
    OracleTransferDTO,
    PostgresTransferDTO,
    S3TransferDTO,
    SFTPTransferDTO,
)
from syncmaster.exceptions.connection import ConnectionTypeNotRecognizedError
from syncmaster.worker.handlers.base import Handler
from syncmaster.worker.handlers.db.clickhouse import ClickhouseHandler
from syncmaster.worker.handlers.db.hive import HiveHandler
from syncmaster.worker.handlers.db.mssql import MSSQLHandler
from syncmaster.worker.handlers.db.mysql import MySQLHandler
from syncmaster.worker.handlers.db.oracle import OracleHandler
from syncmaster.worker.handlers.db.postgres import PostgresHandler
from syncmaster.worker.handlers.file.ftp import FTPHandler
from syncmaster.worker.handlers.file.ftps import FTPSHandler
from syncmaster.worker.handlers.file.hdfs import HDFSHandler
from syncmaster.worker.handlers.file.s3 import S3Handler
from syncmaster.worker.handlers.file.sftp import SFTPHandler
from syncmaster.worker.settings import WorkerAppSettings

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
    "clickhouse": (
        ClickhouseHandler,
        ClickhouseConnectionDTO,
        ClickhouseTransferDTO,
    ),
    "mssql": (
        MSSQLHandler,
        MSSQLConnectionDTO,
        MSSQLTransferDTO,
    ),
    "mysql": (
        MySQLHandler,
        MySQLConnectionDTO,
        MySQLTransferDTO,
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
    "sftp": (
        SFTPHandler,
        SFTPConnectionDTO,
        SFTPTransferDTO,
    ),
    "ftp": (
        FTPHandler,
        FTPConnectionDTO,
        FTPTransferDTO,
    ),
    "ftps": (
        FTPSHandler,
        FTPSConnectionDTO,
        FTPSTransferDTO,
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
    ):
        self.temp_dir = TemporaryDirectory(prefix=f"syncmaster_{run.id}_")

        self.run = run
        self.source_handler = self.get_handler(
            connection_data=source_connection.data,
            transfer_params=run.transfer.source_params,
            transformations=run.transfer.transformations,
            connection_auth_data=source_auth_data,
            temp_dir=TemporaryDirectory(dir=self.temp_dir.name, prefix="downloaded_"),
        )
        self.target_handler = self.get_handler(
            connection_data=target_connection.data,
            transfer_params=run.transfer.target_params,
            transformations=run.transfer.transformations,
            connection_auth_data=target_auth_data,
            temp_dir=TemporaryDirectory(dir=self.temp_dir.name, prefix="written_"),
        )

    def perform_transfer(self, settings: WorkerAppSettings) -> None:
        try:
            spark = settings.worker.CREATE_SPARK_SESSION_FUNCTION(
                run=self.run,
                source=self.source_handler.connection_dto,
                target=self.target_handler.connection_dto,
            )

            with spark:
                self.source_handler.connect(spark)
                self.target_handler.connect(spark)

                df = self.source_handler.read()
                self.target_handler.write(df)
        finally:
            self.temp_dir.cleanup()

    def get_handler(
        self,
        connection_data: dict[str, Any],
        connection_auth_data: dict,
        transfer_params: dict[str, Any],
        transformations: list[dict],
        temp_dir: TemporaryDirectory,
    ) -> Handler:
        connection_data.update(connection_auth_data)
        connection_data.pop("type")
        handler_type = transfer_params.pop("type", None)

        if connection_handler_proxy.get(handler_type, None) is None:
            raise ConnectionTypeNotRecognizedError

        handler, connection_dto, transfer_dto = connection_handler_proxy[handler_type]

        return handler(
            connection_dto=connection_dto(**connection_data),
            transfer_dto=transfer_dto(**transfer_params, transformations=transformations),
            temp_dir=temp_dir,
        )
