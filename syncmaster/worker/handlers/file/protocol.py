# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from onetl.file import FileDFReader, FileDFWriter, FileDownloader, FileUploader
from onetl.file.filter import FileSizeRange, Glob, Regexp

from syncmaster.worker.handlers.file.base import FileHandler

if TYPE_CHECKING:
    from pyspark.sql import DataFrame


class FileProtocolHandler(FileHandler):

    def read(self) -> DataFrame:
        from pyspark.sql.types import StructType

        downloader = FileDownloader(
            connection=self.connection,
            source_path=self.transfer_dto.directory_path,
            local_path=self.temp_dir.name,
            filters=self._get_file_metadata_filters(),
        )
        downloader.run()

        reader = FileDFReader(
            connection=self.local_connection,
            format=self.transfer_dto.file_format,
            source_path=self.temp_dir.name,
            df_schema=StructType.fromJson(self.transfer_dto.df_schema) if self.transfer_dto.df_schema else None,
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
            options={"if_exists": "replace_entire_directory"},
        )
        writer.run(df=df)

        # working with spark generated .crc files may lead to exceptions
        crc_files = [f for f in os.listdir(self.temp_dir.name) if f.endswith(".crc")]
        for file in crc_files:
            os.remove(os.path.join(self.temp_dir.name, file))

        uploader = FileUploader(
            connection=self.connection,
            local_path=self.temp_dir.name,
            target_path=self.transfer_dto.directory_path,
            options=self.transfer_dto.options,
        )
        uploader.run()

    def _make_file_metadata_filters(self, filters: list[dict]) -> list[Glob | Regexp | FileSizeRange]:
        processed_filters = []
        for filter in filters:
            filter_type = filter["type"]
            value = filter["value"]

            if filter_type == "name_glob":
                processed_filters.append(Glob(value))
            elif filter_type == "name_regexp":
                processed_filters.append(Regexp(value))
            elif filter_type == "file_size_min":
                processed_filters.append(FileSizeRange(min=value))
            elif filter_type == "file_size_max":
                processed_filters.append(FileSizeRange(max=value))

        return processed_filters

    def _get_file_metadata_filters(self) -> list[Glob | Regexp | FileSizeRange]:
        expressions = []
        for transformation in self.transfer_dto.transformations:
            if transformation["type"] == "file_metadata_filter":
                expressions.extend(transformation["filters"])

        return self._make_file_metadata_filters(expressions)
