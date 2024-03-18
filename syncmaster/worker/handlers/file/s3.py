# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from onetl.connection import SparkS3

from syncmaster.worker.handlers.file.base import FileHandler


class S3Handler(FileHandler):
    def init_connection(self):
        self.connection = SparkS3(
            host=self.connection_dto.host,
            port=self.connection_dto.port,
            access_key=self.connection_dto.access_key,
            secret_key=self.connection_dto.secret_key,
            bucket=self.connection_dto.bucket,
            protocol=self.connection_dto.protocol,
            region=self.connection_dto.region,
            extra=self.connection_dto.additional_params,
            spark=self.spark,
        ).check()
