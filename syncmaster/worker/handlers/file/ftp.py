# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from syncmaster.dto.connections import FTPConnectionDTO
from syncmaster.worker.handlers.file.local_df import LocalDFFileHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession


class FTPHandler(LocalDFFileHandler):
    connection_dto: FTPConnectionDTO

    def connect(self, spark: SparkSession) -> None:
        from onetl.connection import FTP, SparkLocalFS

        self.file_connection = FTP(
            host=self.connection_dto.host,
            port=self.connection_dto.port,
            user=self.connection_dto.user,
            password=self.connection_dto.password,
        ).check()

        self.local_df_connection = SparkLocalFS(
            spark=spark,
        ).check()
