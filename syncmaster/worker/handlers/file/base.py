# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.base.base_file_df_connection import BaseFileDFConnection
from onetl.file import FileDFReader, FileDFWriter

from syncmaster.dto.connections import ConnectionDTO
from syncmaster.dto.transfers import FileTransferDTO
from syncmaster.worker.handlers.base import Handler

if TYPE_CHECKING:
    from pyspark.sql.dataframe import DataFrame


class FileHandler(Handler):
    connection: BaseFileDFConnection
    connection_dto: ConnectionDTO
    transfer_dto: FileTransferDTO

    def read(self) -> DataFrame:
        from pyspark.sql.types import StructType

        reader = FileDFReader(
            connection=self.connection,
            format=self.transfer_dto.file_format,
            source_path=self.transfer_dto.directory_path,
            df_schema=StructType.fromJson(self.transfer_dto.df_schema) if self.transfer_dto.df_schema else None,
            options=self.transfer_dto.options,
        )

        return reader.run()

    def write(self, df: DataFrame):
        writer = FileDFWriter(
            connection=self.connection,
            format=self.transfer_dto.file_format,
            target_path=self.transfer_dto.directory_path,
            options=self.transfer_dto.options,
        )

        return writer.run(df=df)
