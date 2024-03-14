# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0

from backend.worker.handlers.file.base import FileHandler
from onetl.connection import SparkHDFS


class HDFSHandler(FileHandler):
    def init_connection(self):
        self.connection = SparkHDFS(
            cluster=self.connection_dto.cluster,
            spark=self.spark,
        ).check()
