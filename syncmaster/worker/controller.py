# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import logging
from tempfile import TemporaryDirectory
from typing import Any

from etl_entities.hwm_store import BaseHWMStore
from horizon.client.auth import LoginPassword
from horizon_hwm_store import HorizonHWMStore
from onetl.strategy import IncrementalStrategy

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
    SambaConnectionDTO,
    SFTPConnectionDTO,
    WebDAVConnectionDTO,
)
from syncmaster.dto.runs import RunDTO
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
    SambaTransferDTO,
    SFTPTransferDTO,
    WebDAVTransferDTO,
)
from syncmaster.dto.transfers_resources import Resources
from syncmaster.dto.transfers_strategy import Strategy
from syncmaster.exceptions.connection import ConnectionTypeNotRecognizedError
from syncmaster.schemas.v1.connection_types import FILE_CONNECTION_TYPES
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
from syncmaster.worker.handlers.file.samba import SambaHandler
from syncmaster.worker.handlers.file.sftp import SFTPHandler
from syncmaster.worker.handlers.file.webdav import WebDAVHandler
from syncmaster.worker.settings import WorkerAppSettings

logger = logging.getLogger(__name__)


connection_handler_proxy = {
    "hive": (
        HiveHandler,
        HiveConnectionDTO,
        HiveTransferDTO,
        RunDTO,
    ),
    "oracle": (
        OracleHandler,
        OracleConnectionDTO,
        OracleTransferDTO,
        RunDTO,
    ),
    "clickhouse": (
        ClickhouseHandler,
        ClickhouseConnectionDTO,
        ClickhouseTransferDTO,
        RunDTO,
    ),
    "mssql": (
        MSSQLHandler,
        MSSQLConnectionDTO,
        MSSQLTransferDTO,
        RunDTO,
    ),
    "mysql": (
        MySQLHandler,
        MySQLConnectionDTO,
        MySQLTransferDTO,
        RunDTO,
    ),
    "postgres": (
        PostgresHandler,
        PostgresConnectionDTO,
        PostgresTransferDTO,
        RunDTO,
    ),
    "s3": (
        S3Handler,
        S3ConnectionDTO,
        S3TransferDTO,
        RunDTO,
    ),
    "hdfs": (
        HDFSHandler,
        HDFSConnectionDTO,
        HDFSTransferDTO,
        RunDTO,
    ),
    "sftp": (
        SFTPHandler,
        SFTPConnectionDTO,
        SFTPTransferDTO,
        RunDTO,
    ),
    "ftp": (
        FTPHandler,
        FTPConnectionDTO,
        FTPTransferDTO,
        RunDTO,
    ),
    "ftps": (
        FTPSHandler,
        FTPSConnectionDTO,
        FTPSTransferDTO,
        RunDTO,
    ),
    "samba": (
        SambaHandler,
        SambaConnectionDTO,
        SambaTransferDTO,
        RunDTO,
    ),
    "webdav": (
        WebDAVHandler,
        WebDAVConnectionDTO,
        WebDAVTransferDTO,
        RunDTO,
    ),
}


class TransferController:
    settings: WorkerAppSettings
    source_handler: Handler
    target_handler: Handler

    def __init__(
        self,
        settings: WorkerAppSettings,
        run: Run,
        source_connection: Connection,
        source_auth_data: dict,
        target_connection: Connection,
        target_auth_data: dict,
    ):
        self.temp_dir = TemporaryDirectory(prefix=f"syncmaster_{run.id}_")

        self.settings = settings
        self.run = run
        self.source_handler = self.get_handler(
            connection_data=source_connection.data,
            run_data={"id": run.id, "created_at": run.created_at},
            transfer_id=run.transfer.id,
            transfer_params=run.transfer.source_params,
            strategy_params=run.transfer.strategy_params,
            resources=run.transfer.resources,
            transformations=run.transfer.transformations,
            connection_auth_data=source_auth_data,
            temp_dir=TemporaryDirectory(dir=self.temp_dir.name, prefix="downloaded_"),
        )
        self.target_handler = self.get_handler(
            connection_data=target_connection.data,
            run_data={"id": run.id, "created_at": run.created_at},
            transfer_id=run.transfer.id,
            transfer_params=run.transfer.target_params,
            strategy_params=run.transfer.strategy_params,
            resources=run.transfer.resources,
            transformations=run.transfer.transformations,
            connection_auth_data=target_auth_data,
            temp_dir=TemporaryDirectory(dir=self.temp_dir.name, prefix="written_"),
        )

    def perform_transfer(self) -> None:
        try:
            spark = self.settings.worker.CREATE_SPARK_SESSION_FUNCTION(
                run=self.run,
                source=self.source_handler.connection_dto,
                target=self.target_handler.connection_dto,
            )

            with spark:
                self.source_handler.connect(spark)
                self.target_handler.connect(spark)

                if self.source_handler.transfer_dto.strategy.type == "incremental":
                    return self._perform_incremental_transfer()

                if self.source_handler.transfer_dto.strategy.type == "full" and self.settings.hwm_store.enabled:
                    self._reset_transfer_hwm()

                df = self.source_handler.read()
                self.target_handler.write(df)
        finally:
            self.temp_dir.cleanup()

    def get_handler(
        self,
        connection_data: dict[str, Any],
        connection_auth_data: dict,
        run_data: dict[str, Any],
        transfer_id: int,
        transfer_params: dict[str, Any],
        strategy_params: dict[str, Any],
        resources: dict[str, Any],
        transformations: list[dict],
        temp_dir: TemporaryDirectory,
    ) -> Handler:
        connection_data.update(connection_auth_data)
        connection_data.pop("type")
        handler_type = transfer_params.pop("type", None)

        if connection_handler_proxy.get(handler_type, None) is None:
            raise ConnectionTypeNotRecognizedError

        handler, connection_dto, transfer_dto, run_dto = connection_handler_proxy[handler_type]

        return handler(
            connection_dto=connection_dto(**connection_data),
            transfer_dto=transfer_dto(
                id=transfer_id,
                strategy=Strategy.from_dict(strategy_params),
                resources=Resources(**resources),
                transformations=transformations,
                **transfer_params,
            ),
            run_dto=run_dto(**run_data),
            temp_dir=temp_dir,
        )

    def _get_hwm_store(self) -> BaseHWMStore:
        return HorizonHWMStore(
            api_url=self.settings.hwm_store.url,
            auth=LoginPassword(login=self.settings.hwm_store.user, password=self.settings.hwm_store.password),
            namespace=self.settings.hwm_store.namespace,
        ).force_create_namespace()

    def _perform_incremental_transfer(self) -> None:
        with self._get_hwm_store() as hwm_store:
            with IncrementalStrategy():
                hwm_name = self._get_transfer_hwm_name()
                hwm = hwm_store.get_hwm(hwm_name)

                self.source_handler.hwm = hwm
                self.target_handler.hwm = hwm

                df = self.source_handler.read()
                self.target_handler.write(df)

    def _get_transfer_hwm_name(self) -> str:
        if self.source_handler.connection_dto.type in FILE_CONNECTION_TYPES:
            hwm_name_suffix = self.source_handler.transfer_dto.directory_path
        else:
            hwm_name_suffix = self.source_handler.transfer_dto.table_name
        hwm_name = "_".join(
            [
                str(self.source_handler.transfer_dto.id),
                self.source_handler.connection_dto.type,
                hwm_name_suffix,
            ],
        )
        return hwm_name

    def _reset_transfer_hwm(self) -> None:
        with self._get_hwm_store() as hwm_store:
            hwm_name = self._get_transfer_hwm_name()
            hwm = hwm_store.get_hwm(hwm_name)
            if hwm and hwm.value:
                hwm.reset()
                hwm_store.set_hwm(hwm)
                logger.warning(
                    "HWM value has been reset to its default for transfer with id = %r",
                    self.source_handler.transfer_dto.id,
                )
