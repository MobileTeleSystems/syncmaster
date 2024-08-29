# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.connection import SparkHDFS

from syncmaster.dto.connections import HDFSConnectionDTO
from syncmaster.worker.handlers.file.base import FileHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession


class HDFSHandler(FileHandler):
    connection_dto: HDFSConnectionDTO

    def connect(self, spark: SparkSession):
        self.connection = SparkHDFS(
            cluster=self.connection_dto.cluster,
            spark=spark,
        ).check()
