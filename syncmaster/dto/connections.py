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
    additional_params: dict
    database_name: str
    type: str = "postgres"


@dataclass
class OracleConnectionDTO(ConnectionDTO):
    host: str
    port: int
    user: str
    password: str
    additional_params: dict
    sid: str | None = None
    service_name: str | None = None
    type: str = "oracle"


@dataclass
class HiveConnectionDTO(ConnectionDTO):
    user: str
    password: str
    cluster: str
    type: str = "hive"


@dataclass
class HDFSConnectionDTO(ConnectionDTO):
    user: str
    password: str
    cluster: str
    type: str = "hdfs"


@dataclass
class S3ConnectionDTO(ConnectionDTO):
    host: str
    port: int
    access_key: str
    secret_key: str
    bucket: str
    additional_params: dict
    region: str | None = None
    protocol: str = "https"
    type: str = "s3"
