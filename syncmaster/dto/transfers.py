# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import json
from dataclasses import dataclass, field
from typing import ClassVar
from uuid import uuid4

from onetl.file.format import CSV, JSON, ORC, XML, Excel, JSONLine, Parquet

from syncmaster.dto.transfers_resources import Resources
from syncmaster.dto.transfers_strategy import FullStrategy, IncrementalStrategy


@dataclass
class TransferDTO:
    type: ClassVar[str]
    id: int
    name: str
    group_name: str


@dataclass
class DBTransferDTO(TransferDTO):
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
    directory_path: str
    file_format: CSV | JSONLine | JSON | Excel | XML | ORC | Parquet
    strategy: FullStrategy | IncrementalStrategy
    resources: Resources
    options: dict
    file_name_template: str | None = None
    df_schema: dict | None = None
    transformations: list[dict] | None = None

    _format_parsers: ClassVar[dict] = {
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

    @staticmethod
    def _rewrite_option_name(file_format: dict, from_name: str, to_name: str):  # noqa: WPS602
        if from_name in file_format:
            file_format[to_name] = file_format.pop(from_name)

    def _get_file_format(self, file_format: dict) -> CSV | JSONLine | JSON | Excel | XML | ORC | Parquet:
        file_type = file_format.pop("type", None)
        if file_type == "xml":
            self._rewrite_option_name(file_format, "root_tag", "rootTag")
            self._rewrite_option_name(file_format, "row_tag", "rowTag")
            # XML at spark-xml has no "none" option https://github.com/databricks/spark-xml?tab=readme-ov-file#features
            if file_format.get("compression") == "none":
                file_format.pop("compression")

        if file_type == "excel":
            self._rewrite_option_name(file_format, "include_header", "header")
            self._rewrite_option_name(file_format, "start_cell", "dataAddress")

        if file_type == "csv":
            self._rewrite_option_name(file_format, "line_sep", "lineSep")
            self._rewrite_option_name(file_format, "include_header", "header")

        if file_type in {"json", "jsonline"}:
            self._rewrite_option_name(file_format, "line_sep", "lineSep")

        parser_class = self._format_parsers.get(file_type)
        if parser_class is not None:
            return parser_class.parse_obj(file_format)

        msg = f"Unknown file type: {file_type}"
        raise ValueError(msg)


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
class IcebergTransferDTO(DBTransferDTO):
    type: ClassVar[str] = "iceberg"
    catalog_name: str = field(default_factory=lambda: f"iceberg_{uuid4().hex[:8]}")  # noqa: WPS237

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
