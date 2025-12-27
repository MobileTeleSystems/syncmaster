# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from etl_entities.hwm import FileHWM, FileListHWM, FileModifiedTimeHWM
from onetl.file import FileDFReader, FileDFWriter, FileDownloader, FileUploader
from onetl.file.filter import FileSizeRange, Glob, Regexp

from syncmaster.dto.transfers_strategy import IncrementalStrategy
from syncmaster.worker.handlers.file.base import FileHandler

if TYPE_CHECKING:
    from onetl.connection import SparkLocalFS
    from pyspark.sql import DataFrame


class LocalDFFileHandler(FileHandler):
    local_df_connection: SparkLocalFS

    def read(self) -> DataFrame:
        from pyspark.sql.types import StructType  # noqa: PLC0415

        downloader_params: dict[str, FileHWM] = {}
        if isinstance(self.transfer_dto.strategy, IncrementalStrategy):
            hwm_name = f"{self.transfer_dto.id}_{self.connection_dto.type}_{self.transfer_dto.directory_path}"
            if self.transfer_dto.strategy.increment_by == "file_modified_since":
                downloader_params["hwm"] = FileModifiedTimeHWM(name=hwm_name)
            elif self.transfer_dto.strategy.increment_by == "file_name":
                downloader_params["hwm"] = FileListHWM(name=hwm_name)

        downloader = FileDownloader(
            connection=self.file_connection,
            source_path=self.transfer_dto.directory_path,
            local_path=self.temp_dir.name,
            filters=self._get_file_metadata_filters(),
            **downloader_params,
        )

        downloader.run()

        reader = FileDFReader(
            connection=self.local_df_connection,
            format=self.transfer_dto.file_format,
            source_path=self.temp_dir.name,
            df_schema=(StructType.fromJson(self.transfer_dto.df_schema) if self.transfer_dto.df_schema else None),
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
            connection=self.local_df_connection,
            format=self.transfer_dto.file_format,
            target_path=self.temp_dir.name,
            options=self.transfer_dto.options,
        )
        writer.run(df=df)

        # working with spark generated .crc files may lead to exceptions
        crc_files = [f for f in Path(self.temp_dir.name).iterdir() if f.name.endswith(".crc")]
        for file in crc_files:
            file.unlink()

        self._rename_files()

        uploader = FileUploader(
            connection=self.file_connection,
            local_path=self.temp_dir.name,
            target_path=self.transfer_dto.directory_path,
        )
        uploader.run()

    def _rename_files(self):
        tmp_dir = Path(self.temp_dir.name)
        for index, file_name in enumerate(tmp_dir.iterdir()):
            extension = self._get_file_extension()
            new_name = self._get_file_name(index, extension)
            old_path = Path(self.temp_dir.name, file_name)
            new_path = Path(self.temp_dir.name, new_name)
            old_path.rename(new_path)

    def _make_file_metadata_filters(self, filters: list[dict]) -> list[Glob | Regexp | FileSizeRange]:
        processed_filters = []
        for filter_ in filters:
            filter_type = filter_["type"]
            value = filter_["value"]

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
