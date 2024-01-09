# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass


@dataclass
class ConnectionDTO:
    pass


@dataclass
class PostgresConnectionDTO(ConnectionDTO):
    host: str
    port: int
    user: str
    password: str
    database_name: str
    additional_params: dict
    type: str = "postgres"


@dataclass
class OracleConnectionDTO(ConnectionDTO):
    host: str
    port: int
    user: str
    password: str
    sid: str | None
    service_name: str | None
    additional_params: dict
    type: str = "oracle"


@dataclass
class HiveConnectionDTO(ConnectionDTO):
    cluster: str
    additional_params: dict
    user: str
    password: str
    type: str = "hive"
