# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from onetl.base.base_file_df_connection import BaseFileDFConnection
from onetl.file import FileDFReader, FileDFWriter, FileMover
from onetl.file.filter import Glob

from syncmaster.dto.connections import ConnectionDTO
from syncmaster.dto.transfers import FileTransferDTO
from syncmaster.worker.handlers.base import Handler

if TYPE_CHECKING:
    from pyspark.sql.dataframe import DataFrame

COLUMN_FORMATS = ("parquet", "orc")


class FileHandler(Handler):
    """
    TODO: FileHandler is actually handler for FileDFWriter with remote FS (direct write).
    FileProtocolHandler is handler for FileDFWriter with local FS (write via upload).
    Maybe we should keep here only common methods,
    like file name generator and split other ones to classes where the method is really used.
    """

    df_connection: BaseFileDFConnection
    connection_dto: ConnectionDTO
    transfer_dto: FileTransferDTO
    _operators = {
        "is_null": "IS NULL",
        "is_not_null": "IS NOT NULL",
        "equal": "=",
        "not_equal": "!=",
        "greater_than": ">",
        "greater_or_equal": ">=",
        "less_than": "<",
        "less_or_equal": "<=",
        "like": "LIKE",
        "ilike": "ILIKE",
        "not_like": "NOT LIKE",
        "not_ilike": "NOT ILIKE",
        "regexp": "RLIKE",
    }
    _compression_to_file_suffix = {
        "gzip": "gz",
        "snappy": "snappy",
        "zlib": "zlib",
        "lz4": "lz4",
        "bzip2": "bz2",
        "deflate": "deflate",
    }
    _file_format_to_file_suffix = {
        "json": "json",
        "jsonline": "jsonl",
        "csv": "csv",
        "xml": "xml",
        "excel": "xlsx",
        "parquet": "parquet",
        "orc": "orc",
    }

    def read(self) -> DataFrame:
        from pyspark.sql.types import StructType

        reader = FileDFReader(
            connection=self.df_connection,
            format=self.transfer_dto.file_format,
            source_path=self.transfer_dto.directory_path,
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
        tmp_path = os.path.join(self.transfer_dto.directory_path, ".tmp", str(self.run_dto.id))
        try:
            writer = FileDFWriter(
                connection=self.df_connection,
                format=self.transfer_dto.file_format,
                target_path=tmp_path,
                options=self.transfer_dto.options,
            )
            writer.run(df=df)

            self._rename_files(tmp_path)

            mover = FileMover(
                connection=self.file_connection,
                source_path=tmp_path,
                target_path=self.transfer_dto.directory_path,
                # ignore .crc and other metadata files
                filters=[Glob(f"*.{self._get_file_extension()}")],
            )
            mover.run()
        finally:
            self.file_connection.remove_dir(tmp_path, recursive=True)

    def _rename_files(self, tmp_path: str) -> None:
        files = self.file_connection.list_dir(tmp_path)

        for index, file_name in enumerate(files):
            extension = self._get_file_extension()
            new_name = self._get_file_name(str(index), extension)
            old_path = os.path.join(tmp_path, file_name)
            new_path = os.path.join(tmp_path, new_name)
            self.file_connection.rename_file(old_path, new_path)

    def _get_file_name(self, index: str, extension: str) -> str:
        return self.transfer_dto.file_name_template.format(
            index=index,
            extension=extension,
            run_id=self.run_dto.id,
            run_created_at=self.run_dto.created_at.strftime("%Y_%m_%d_%H_%M_%S"),
        )

    def _get_file_extension(self) -> str:
        file_format = self.transfer_dto.file_format.__class__.__name__.lower()
        extension_suffix = self._file_format_to_file_suffix[file_format]

        compression = getattr(self.transfer_dto.file_format, "compression", "none")
        if compression == "none":
            return extension_suffix

        compression_suffix = self._compression_to_file_suffix[compression]

        # https://github.com/apache/parquet-java/blob/fb6f0be0323f5f52715b54b8c6602763d8d0128d/parquet-common/src/main/java/org/apache/parquet/hadoop/metadata/CompressionCodecName.java#L26-L33
        if extension_suffix == "parquet" and compression_suffix == "lz4":
            return "lz4hadoop.parquet"

        if extension_suffix in COLUMN_FORMATS:
            return f"{compression_suffix}.{extension_suffix}"

        return f"{extension_suffix}.{compression_suffix}"

    def _make_rows_filter_expression(self, filters: list[dict]) -> str | None:
        expressions = []
        for filter in filters:
            field = filter["field"]
            op = self._operators[filter["type"]]
            value = filter.get("value")

            expressions.append(f"{field} {op} '{value}'" if value is not None else f"{field} {op}")

        return " AND ".join(expressions) or None

    def _make_columns_filter_expressions(self, filters: list[dict]) -> list[str] | None:
        # TODO: another approach is to use df.select(col("col1"), col("col2").alias("new_col2"), ...)
        expressions = []
        for filter in filters:
            filter_type = filter["type"]
            field = filter["field"]

            if filter_type == "include":
                expressions.append(field)
            elif filter_type == "rename":
                new_name = filter["to"]
                expressions.append(f"{field} AS {new_name}")
            elif filter_type == "cast":
                cast_type = filter["as_type"]
                expressions.append(f"CAST({field} AS {cast_type}) AS {field}")

        return expressions or None

    def _get_rows_filter_expression(self) -> str | None:
        expressions = []
        for transformation in self.transfer_dto.transformations:
            if transformation["type"] == "dataframe_rows_filter":
                expressions.extend(transformation["filters"])

        return self._make_rows_filter_expression(expressions)

    def _get_columns_filter_expressions(self) -> list[str] | None:
        expressions = []
        for transformation in self.transfer_dto.transformations:
            if transformation["type"] == "dataframe_columns_filter":
                expressions.extend(transformation["filters"])

        return self._make_columns_filter_expressions(expressions)
