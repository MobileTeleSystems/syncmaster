# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.connection import HDFS, SparkHDFS

from syncmaster.dto.connections import HDFSConnectionDTO
from syncmaster.worker.handlers.file.remote_df import RemoteDFFileHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession


class HDFSHandler(RemoteDFFileHandler):
    connection_dto: HDFSConnectionDTO

    def connect(self, spark: SparkSession):
        self.df_connection = SparkHDFS(
            cluster=self.connection_dto.cluster,
            spark=spark,
        ).check()
        self.file_connection = HDFS(
            cluster=self.connection_dto.cluster,
        ).check()
