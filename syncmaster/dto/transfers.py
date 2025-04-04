# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import json
from dataclasses import dataclass
from typing import ClassVar

from onetl.file.format import CSV, JSON, ORC, XML, Excel, JSONLine, Parquet

from syncmaster.dto.transfers_resources import Resources
from syncmaster.dto.transfers_strategy import FullStrategy, IncrementalStrategy


@dataclass
class TransferDTO:
    type: ClassVar[str]


@dataclass
class DBTransferDTO(TransferDTO):
    id: int
    table_name: str
    strategy: FullStrategy | IncrementalStrategy
    resources: Resources
    transformations: list[dict] | None = None
    options: dict | None = None

    def __post_init__(self):
        if self.options is None:
            self.options = {}
        self.options.setdefault("if_exists", "replace_entire_table")


@dataclass
class FileTransferDTO(TransferDTO):
    id: int
    directory_path: str
    file_format: CSV | JSONLine | JSON | Excel | XML | ORC | Parquet
    strategy: FullStrategy | IncrementalStrategy
    resources: Resources
    options: dict
    file_name_template: str | None = None
    df_schema: dict | None = None
    transformations: list[dict] | None = None

    _format_parsers = {
        "csv": CSV,
        "jsonline": JSONLine,
        "json": JSON,
        "excel": Excel,
        "orc": ORC,
        "parquet": Parquet,
        "xml": XML,
    }

    def __post_init__(self):
        if isinstance(self.file_format, dict):
            self.file_format = self._get_file_format(self.file_format.copy())
        if isinstance(self.df_schema, str):
            self.df_schema = json.loads(self.df_schema)

        self.options.setdefault("if_exists", "replace_overlapping_partitions")

    def _get_file_format(self, file_format: dict) -> CSV | JSONLine | JSON | Excel | XML | ORC | Parquet:
        file_type = file_format.pop("type", None)
        # XML at spark-xml has no "none" option https://github.com/databricks/spark-xml?tab=readme-ov-file#features
        if file_type == "xml" and file_format.get("compression") == "none":
            file_format.pop("compression")

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

    def __post_init__(self):
        super().__post_init__()
        self.options.setdefault("if_exists", "replace_overlapping_partitions")


@dataclass
class S3TransferDTO(FileTransferDTO):
    type: ClassVar[str] = "s3"


@dataclass
class HDFSTransferDTO(FileTransferDTO):
    type: ClassVar[str] = "hdfs"


@dataclass
class SFTPTransferDTO(FileTransferDTO):
    type: ClassVar[str] = "sftp"


@dataclass
class FTPTransferDTO(FileTransferDTO):
    type: ClassVar[str] = "ftp"


@dataclass
class FTPSTransferDTO(FileTransferDTO):
    type: ClassVar[str] = "ftps"


@dataclass
class SambaTransferDTO(FileTransferDTO):
    type: ClassVar[str] = "samba"


@dataclass
class WebDAVTransferDTO(FileTransferDTO):
    type: ClassVar[str] = "webdav"
