# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
import json

from onetl.base.base_file_df_connection import BaseFileDFConnection
from onetl.file import FileDFReader, FileDFWriter
from onetl.file.format import CSV, JSON, JSONLine
from pyspark.sql.dataframe import DataFrame
from pyspark.sql.types import StructType

from syncmaster.dto.connections import ConnectionDTO
from syncmaster.dto.transfers import TransferDTO
from syncmaster.worker.handlers.base import Handler


class FileHandler(Handler):
    connection: BaseFileDFConnection
    connection_dto: ConnectionDTO
    transfer_dto: TransferDTO

    def init_connection(self): ...

    def init_reader(self):
        super().init_reader()

        self.reader = FileDFReader(
            connection=self.connection,
            format=self._get_format(),
            source_path=self.transfer_dto.directory_path,
            df_schema=StructType.fromJson(json.loads(self.transfer_dto.df_schema)),
            options=self.transfer_dto.options,
        )

    def init_writer(self):
        super().init_writer()

        self.writer = FileDFWriter(
            connection=self.connection,
            format=self._get_format(),
            target_path=self.transfer_dto.directory_path,
            options=self.transfer_dto.options,
        )

    def normalize_column_name(self, df: DataFrame) -> DataFrame:
        return df

    def _get_format(self):
        file_type = self.transfer_dto.file_format["type"]
        if file_type == "csv":
            return CSV.parse_obj(self.transfer_dto.file_format)
        elif file_type == "jsonline":
            return JSONLine.parse_obj(self.transfer_dto.file_format)
        elif file_type == "json":
            return JSON.parse_obj(self.transfer_dto.file_format)
        else:
            raise ValueError("Unknown file type")
