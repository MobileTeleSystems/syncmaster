# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from typing import ClassVar, Literal


@dataclass
class ConnectionDTO:
    type: ClassVar[str]


@dataclass
class PostgresConnectionDTO(ConnectionDTO):
    host: str
    port: int
    user: str
    password: str
    additional_params: dict
    database_name: str
    type: ClassVar[str] = "postgres"


@dataclass
class ClickhouseConnectionDTO(ConnectionDTO):
    host: str
    port: int
    user: str
    password: str
    database_name: str
    additional_params: dict
    type: ClassVar[str] = "clickhouse"


@dataclass
class MSSQLConnectionDTO(ConnectionDTO):
    host: str
    port: int
    user: str
    password: str
    database_name: str
    additional_params: dict
    type: ClassVar[str] = "mssql"


@dataclass
class MySQLConnectionDTO(ConnectionDTO):
    host: str
    port: int
    user: str
    password: str
    database_name: str
    additional_params: dict
    type: ClassVar[str] = "mysql"


@dataclass
class OracleConnectionDTO(ConnectionDTO):
    host: str
    port: int
    user: str
    password: str
    additional_params: dict
    sid: str | None = None
    service_name: str | None = None
    type: ClassVar[str] = "oracle"


@dataclass
class HiveConnectionDTO(ConnectionDTO):
    user: str
    password: str
    cluster: str
    type: ClassVar[str] = "hive"


@dataclass
class HDFSConnectionDTO(ConnectionDTO):
    user: str
    password: str
    cluster: str
    type: ClassVar[str] = "hdfs"


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
    type: ClassVar[str] = "s3"


@dataclass
class SFTPConnectionDTO(ConnectionDTO):
    host: str
    port: int
    user: str
    password: str
    type: ClassVar[str] = "sftp"


@dataclass
class FTPConnectionDTO(ConnectionDTO):
    host: str
    port: int
    user: str
    password: str
    type: ClassVar[str] = "ftp"


@dataclass
class FTPSConnectionDTO(ConnectionDTO):
    host: str
    port: int
    user: str
    password: str
    type: ClassVar[str] = "ftps"


@dataclass
class SambaConnectionDTO(ConnectionDTO):
    host: str
    share: str
    protocol: Literal["SMB", "NetBIOS"]
    user: str
    password: str
    auth_type: Literal["NTLMv1", "NTLMv2"] = "NTLMv2"
    domain: str = ""
    port: int | None = None
    type: ClassVar[str] = "samba"


@dataclass
class WebDAVConnectionDTO(ConnectionDTO):
    host: str
    port: int
    user: str
    password: str
    protocol: Literal["http", "https"] = "https"
    type: ClassVar[str] = "webdav"
