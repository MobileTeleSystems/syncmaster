# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from onetl.file import FileDFReader, FileDFWriter, FileMover
from onetl.file.filter import Glob

from syncmaster.worker.handlers.file.base import FileHandler

if TYPE_CHECKING:
    from pyspark.sql import DataFrame


class RemoteDFFileHandler(FileHandler):

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
