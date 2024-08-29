# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.connection import SparkS3

from syncmaster.dto.connections import S3ConnectionDTO
from syncmaster.worker.handlers.file.base import FileHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession


class S3Handler(FileHandler):
    connection_dto: S3ConnectionDTO

    def connect(self, spark: SparkSession):
        self.connection = SparkS3(
            host=self.connection_dto.host,
            port=self.connection_dto.port,
            access_key=self.connection_dto.access_key,
            secret_key=self.connection_dto.secret_key,
            bucket=self.connection_dto.bucket,
            protocol=self.connection_dto.protocol,
            region=self.connection_dto.region,
            extra=self.connection_dto.additional_params,
            spark=spark,
        ).check()
