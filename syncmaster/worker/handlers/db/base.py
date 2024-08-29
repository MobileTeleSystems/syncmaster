# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from onetl.base import BaseDBConnection
from onetl.db import DBReader, DBWriter

from syncmaster.dto.transfers import DBTransferDTO
from syncmaster.worker.handlers.base import Handler

if TYPE_CHECKING:
    from pyspark.sql.dataframe import DataFrame


class DBHandler(Handler):
    connection: BaseDBConnection
    transfer_dto: DBTransferDTO

    def read(self) -> DataFrame:
        reader = DBReader(
            connection=self.connection,
            table=self.transfer_dto.table_name,
        )
        return reader.run()

    def write(self, df: DataFrame) -> None:
        writer = DBWriter(
            connection=self.connection,
            table=self.transfer_dto.table_name,
        )
        return writer.run(df=self.normalize_column_names(df))

    @abstractmethod
    def normalize_column_names(self, df: DataFrame) -> DataFrame: ...
