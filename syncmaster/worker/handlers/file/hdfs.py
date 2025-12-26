# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.hooks import slot, support_hooks

from syncmaster.worker.handlers.file.remote_df import RemoteDFFileHandler

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession

    from syncmaster.dto.connections import HDFSConnectionDTO


@support_hooks
class HDFSHandler(RemoteDFFileHandler):
    connection_dto: HDFSConnectionDTO

    def connect(self, spark: SparkSession):
        from onetl.connection import HDFS, SparkHDFS

        self.df_connection = SparkHDFS(
            cluster=self.connection_dto.cluster,
            spark=spark,
        ).check()

        self.file_connection = HDFS(
            cluster=self.connection_dto.cluster,
            user=self.connection_dto.user,
            password=self.connection_dto.password,
        ).check()

    @slot
    def read(self) -> DataFrame:
        return super().read()

    @slot
    def write(self, df: DataFrame) -> None:
        return super().write(df)
