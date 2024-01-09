# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass


@dataclass
class PostgresTransferParamsDTO:
    table_name: str
    type: str = "postgres"


@dataclass
class OracleTransferParamsDTO:
    table_name: str
    type: str = "oracle"


@dataclass
class HiveTransferParamsDTO:
    table_name: str
    type: str = "hive"
