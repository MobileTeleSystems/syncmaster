# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from syncmaster.dto.connections import ConnectionDTO
from syncmaster.dto.transfers import TransferDTO

if TYPE_CHECKING:
    from pyspark.sql import SparkSession
    from pyspark.sql.dataframe import DataFrame


class Handler(ABC):
    def __init__(
        self,
        connection_dto: ConnectionDTO,
        transfer_dto: TransferDTO,
    ):
        self.connection_dto = connection_dto
        self.transfer_dto = transfer_dto

    @abstractmethod
    def connect(self, spark: SparkSession) -> None: ...

    @abstractmethod
    def read(self) -> DataFrame: ...

    @abstractmethod
    def write(self, df: DataFrame) -> None: ...
