# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from syncmaster.schemas.v1.transfers.file_format import CSV, JSON, JSONLine


@dataclass
class TransferDTO:
    pass


@dataclass
class PostgresTransferDTO(TransferDTO):
    table_name: str
    type: str = "postgres"


@dataclass
class OracleTransferDTO(TransferDTO):
    table_name: str
    type: str = "oracle"


@dataclass
class HiveTransferDTO(TransferDTO):
    table_name: str
    type: str = "hive"


@dataclass
class S3TransferDTO(TransferDTO):
    directory_path: str
    file_format: CSV | JSONLine | JSON
    options: dict
    df_schema: dict | None = None
    type: str = "s3"


@dataclass
class HDFSTransferDTO(TransferDTO):
    directory_path: str
    file_format: CSV | JSONLine | JSON
    options: dict
    df_schema: dict | None = None
    type: str = "hdfs"
