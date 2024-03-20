# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0

from onetl.connection import SparkHDFS

from syncmaster.worker.handlers.file.base import FileHandler


class HDFSHandler(FileHandler):
    def init_connection(self):
        self.connection = SparkHDFS(
            cluster=self.connection_dto.cluster,
            spark=self.spark,
        ).check()
