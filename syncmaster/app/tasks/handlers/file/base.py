# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from typing import Union

import pydantic
from onetl.base.base_file_df_connection import BaseFileDFConnection
from onetl.file import FileDFReader
from onetl.file.format import CSV, JSON
from pyspark.sql.dataframe import DataFrame

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
        file_format = pydantic.parse_obj_as(Union[CSV, JSON], self.transfer_params.file_format)

        self.reader = FileDFReader(
            connection=self.connection,
            format=file_format,
            source_path=self.transfer_params.directory_path,
            df_schema=self.transfer_params.df_schema,
            options=self.transfer_params.options,
        )

    def init_writer(self):
        pass

    def normalize_column_name(self, df: DataFrame) -> DataFrame:  # type: ignore
        return df
