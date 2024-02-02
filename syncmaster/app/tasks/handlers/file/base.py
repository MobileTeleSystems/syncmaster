# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
import json

import pydantic
from onetl.base.base_file_df_connection import BaseFileDFConnection
from onetl.file import FileDFReader, FileDFWriter
from onetl.file.format import CSV, JSONLine
from pyspark.sql.dataframe import DataFrame
from pyspark.sql.types import StructType

from app.dto.connections import ConnectionDTO
from app.dto.transfers import TransferDTO
from app.tasks.handlers.base import Handler


class FileHandler(Handler):
    connection: BaseFileDFConnection
    connection_dto: ConnectionDTO
    transfer_params: TransferDTO

    def init_connection(self):
        ...

    def init_reader(self):
        super().init_reader()

        self.reader = FileDFReader(
            connection=self.connection,
            format=self._get_format(),
            source_path=self.transfer_params.directory_path,
            df_schema=StructType.fromJson(json.loads(self.transfer_params.df_schema)),
            options=self.transfer_params.options,
        )

    def init_writer(self):
        super().init_writer()

        self.writer = FileDFWriter(
            connection=self.connection,
            format=self._get_format(),
            target_path=self.transfer_params.directory_path,
            options=self.transfer_params.options,
        )

    def normalize_column_name(self, df: DataFrame) -> DataFrame:  # type: ignore
        return df

    def _get_format(self):
        file_type = self.transfer_params.file_format["type"]
        if file_type == "csv":
            return pydantic.parse_obj_as(CSV, self.transfer_params.file_format)
        elif file_type == "jsonline":
            return pydantic.parse_obj_as(JSONLine, self.transfer_params.file_format)
        else:
            raise ValueError("Unknown file type")
