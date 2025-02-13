# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.connection import Samba, SparkLocalFS

from syncmaster.dto.connections import SambaConnectionDTO
from syncmaster.worker.handlers.file.protocol import FileProtocolHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession


class SambaHandler(FileProtocolHandler):
    connection_dto: SambaConnectionDTO

    def connect(self, spark: SparkSession) -> None:
        self.file_connection = Samba(
            host=self.connection_dto.host,
            port=self.connection_dto.port,
            share=self.connection_dto.share,
            protocol=self.connection_dto.protocol,
            domain=self.connection_dto.domain,
            user=self.connection_dto.user,
            password=self.connection_dto.password,
            auth_type=self.connection_dto.auth_type,
        ).check()
        self.local_df_connection = SparkLocalFS(
            spark=spark,
        ).check()
