# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.connection import SFTP, SparkLocalFS
from onetl.file import FileDFReader, FileDFWriter, FileDownloader, FileUploader

from syncmaster.dto.connections import SFTPConnectionDTO
from syncmaster.worker.handlers.file.base import FileHandler

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession


class SFTPHandler(FileHandler):
    connection_dto: SFTPConnectionDTO

    def connect(self, spark: SparkSession) -> None:
        self.connection = SFTP(
            host=self.connection_dto.host,
            port=self.connection_dto.port,
            user=self.connection_dto.user,
            password=self.connection_dto.password,
            compress=False,  # to avoid errors from combining file and SCP-level compression
        ).check()
        self.local_connection = SparkLocalFS(
            spark=spark,
        ).check()

    def read(self) -> DataFrame:
        from pyspark.sql.types import StructType

        downloader = FileDownloader(
            connection=self.connection,
            source_path=self.transfer_dto.directory_path,
            local_path=self.temp_dir.name,
        )
        downloader.run()

        reader = FileDFReader(
            connection=self.local_connection,
            format=self.transfer_dto.file_format,
            source_path=self.temp_dir.name,
            df_schema=StructType.fromJson(self.transfer_dto.df_schema) if self.transfer_dto.df_schema else None,
            options=self.transfer_dto.options,
        )
        df = reader.run()

        rows_filter_expression = self._get_rows_filter_expression()
        if rows_filter_expression:
            df = df.where(rows_filter_expression)

        columns_filter_expressions = self._get_columns_filter_expressions()
        if columns_filter_expressions:
            df = df.selectExpr(*columns_filter_expressions)

        return df

    def write(self, df: DataFrame) -> None:
        writer = FileDFWriter(
            connection=self.local_connection,
            format=self.transfer_dto.file_format,
            target_path=self.temp_dir.name,
            options=self.transfer_dto.options,
        )
        writer.run(df=df)

        uploader = FileUploader(
            connection=self.connection,
            local_path=self.temp_dir.name,
            target_path=self.transfer_dto.directory_path,
        )
        uploader.run()
