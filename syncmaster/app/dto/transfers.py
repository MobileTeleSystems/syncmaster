# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from app.api.v1.transfers.schemas.file_format import CSV, JSONLine


@dataclass
class TransferDTO:
    pass


@dataclass
class PostgresTransferParamsDTO(TransferDTO):
    table_name: str
    type: str = "postgres"


@dataclass
class OracleTransferParamsDTO(TransferDTO):
    table_name: str
    type: str = "oracle"


@dataclass
class HiveTransferParamsDTO(TransferDTO):
    table_name: str
    type: str = "hive"


@dataclass
class S3TransferParamsDTO(TransferDTO):
    directory_path: str
    file_format: CSV | JSONLine
    options: dict
    df_schema: dict | None = None
    type: str = "s3"
