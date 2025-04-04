# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from syncmaster.dto.connections import FTPSConnectionDTO
from syncmaster.worker.handlers.file.local_df import LocalDFFileHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession


class FTPSHandler(LocalDFFileHandler):
    connection_dto: FTPSConnectionDTO

    def connect(self, spark: SparkSession) -> None:
        from onetl.connection import FTPS, SparkLocalFS

        self.file_connection = FTPS(
            host=self.connection_dto.host,
            port=self.connection_dto.port,
            user=self.connection_dto.user,
            password=self.connection_dto.password,
        ).check()

        self.local_df_connection = SparkLocalFS(
            spark=spark,
        ).check()
