# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tempfile import TemporaryDirectory

    from etl_entities.hwm import HWM
    from pyspark.sql import SparkSession
    from pyspark.sql.dataframe import DataFrame

    from syncmaster.dto.connections import ConnectionDTO
    from syncmaster.dto.runs import RunDTO
    from syncmaster.dto.transfers import DBTransferDTO, FileTransferDTO


class Handler(ABC):
    hwm: HWM | None = None

    def __init__(
        self,
        connection_dto: ConnectionDTO,
        transfer_dto: DBTransferDTO | FileTransferDTO,
        run_dto: RunDTO,
        temp_dir: TemporaryDirectory,
    ):
        self.connection_dto = connection_dto
        self.transfer_dto = transfer_dto
        self.run_dto = run_dto
        self.temp_dir = temp_dir

    @abstractmethod
    def connect(self, spark: SparkSession) -> None: ...

    @abstractmethod
    def read(self) -> DataFrame: ...

    @abstractmethod
    def write(self, df: DataFrame) -> None: ...
