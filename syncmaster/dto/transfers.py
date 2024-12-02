# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import json
from dataclasses import dataclass
from typing import ClassVar

from onetl.file.format import CSV, JSON, Excel, JSONLine


@dataclass
class TransferDTO:
    type: ClassVar[str]


@dataclass
class DBTransferDTO(TransferDTO):
    table_name: str


@dataclass
class FileTransferDTO(TransferDTO):
    directory_path: str
    file_format: CSV | JSONLine | JSON | Excel
    options: dict
    df_schema: dict | None = None

    _format_parsers = {
        "csv": CSV,
        "jsonline": JSONLine,
        "json": JSON,
        "excel": Excel,
    }

    def __post_init__(self):
        if isinstance(self.file_format, dict):
            self.file_format = self._get_format(self.file_format.copy())
        if isinstance(self.df_schema, str):
            self.df_schema = json.loads(self.df_schema)

    def _get_format(self, file_format: dict):
        file_type = file_format.pop("type", None)
        parser_class = self._format_parsers.get(file_type)
        if parser_class is not None:
            return parser_class.parse_obj(file_format)
        raise ValueError(f"Unknown file type: {file_type}")


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
class MySQLTransferDTO(DBTransferDTO):
    type: ClassVar[str] = "mysql"


@dataclass
class HiveTransferDTO(DBTransferDTO):
    type: ClassVar[str] = "hive"


@dataclass
class S3TransferDTO(FileTransferDTO):
    type: ClassVar[str] = "s3"


@dataclass
class HDFSTransferDTO(FileTransferDTO):
    type: ClassVar[str] = "hdfs"
