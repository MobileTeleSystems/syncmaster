# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import json
from dataclasses import dataclass
from typing import ClassVar

from onetl.file.format import CSV, JSON, JSONLine


@dataclass
class TransferDTO:
    type: ClassVar[str]


@dataclass
class DBTransferDTO(TransferDTO):
    table_name: str


@dataclass
class FileTransferDTO(TransferDTO):
    directory_path: str
    file_format: CSV | JSONLine | JSON
    options: dict
    df_schema: dict | None = None

    def __post_init__(self):
        if isinstance(self.file_format, dict):
            self.file_format = self._get_format(self.file_format.copy())
        if isinstance(self.df_schema, str):
            self.df_schema = json.loads(self.df_schema)

    def _get_format(self, file_format: dict):
        file_type = file_format.pop("type", None)
        if file_type == "csv":
            return CSV.parse_obj(file_format)
        if file_type == "jsonline":
            return JSONLine.parse_obj(file_format)
        if file_type == "json":
            return JSON.parse_obj(file_format)
        raise ValueError("Unknown file type")


@dataclass
class PostgresTransferDTO(DBTransferDTO):
    type: ClassVar[str] = "postgres"


@dataclass
class OracleTransferDTO(DBTransferDTO):
    type: ClassVar[str] = "oracle"


@dataclass
class ClickhouseTransferDTO(DBTransferDTO):
    type: ClassVar[str] = "clickhouse"


@dataclass
class MSSQLTransferDTO(DBTransferDTO):
    type: ClassVar[str] = "mssql"


@dataclass
class HiveTransferDTO(DBTransferDTO):
    type: ClassVar[str] = "hive"


@dataclass
class S3TransferDTO(FileTransferDTO):
    type: ClassVar[str] = "s3"


@dataclass
class HDFSTransferDTO(FileTransferDTO):
    type: ClassVar[str] = "hdfs"
