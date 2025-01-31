# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.connection import FTPS, SparkLocalFS

from syncmaster.dto.connections import FTPSConnectionDTO
from syncmaster.worker.handlers.file.protocol import FileProtocolHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession


class FTPSHandler(FileProtocolHandler):
    connection_dto: FTPSConnectionDTO

    def connect(self, spark: SparkSession) -> None:
        self.connection = FTPS(
            host=self.connection_dto.host,
            port=self.connection_dto.port,
            user=self.connection_dto.user,
            password=self.connection_dto.password,
        ).check()
        self.local_connection = SparkLocalFS(
            spark=spark,
        ).check()
