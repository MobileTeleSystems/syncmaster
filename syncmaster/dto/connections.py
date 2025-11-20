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
class IcebergConnectionBaseDTO(ConnectionDTO):
    rest_catalog_url: str
    flavor: ClassVar[str]
    type: ClassVar[str] = "iceberg"


@dataclass
class IcebergRESTCatalogS3DirectConnectionBaseDTO(IcebergConnectionBaseDTO):
    s3_warehouse_path: str
    s3_host: str
    s3_bucket: str
    s3_bucket_style: Literal["domain", "path"]
    s3_region: str
    s3_access_key: str
    s3_secret_key: str
    s3_port: int | None
    s3_protocol: str
    s3_additional_params: dict
    implementation: ClassVar[str] = "iceberg_rest_s3_direct"


@dataclass(kw_only=True)
class IcebergRESTCatalogBasicAuthS3BasicDTO(IcebergRESTCatalogS3DirectConnectionBaseDTO):
    rest_catalog_username: str
    rest_catalog_password: str
    rest_catalog_auth_type: Literal["basic"] = "basic"


@dataclass(kw_only=True)
class IcebergRESTCatalogOAuth2ClientCredentialsS3BasicDTO(IcebergRESTCatalogS3DirectConnectionBaseDTO):
    rest_catalog_oauth2_client_id: str
    rest_catalog_oauth2_client_secret: str
    rest_catalog_oauth2_scopes: list[str]
    rest_catalog_oauth2_resource: str | None = None
    rest_catalog_oauth2_audience: str | None = None
    rest_catalog_oauth2_token_endpoint: str | None = None
    rest_catalog_auth_type: Literal["oauth2"] = "oauth2"


@dataclass
class IcebergRESTCatalogS3DelegatedConnectionBaseDTO(IcebergConnectionBaseDTO):
    s3_warehouse_name: str | None = None
    s3_access_delegation: Literal["vended-credentials", "remote-signing"] = "vended-credentials"
    implementation: ClassVar[str] = "iceberg_rest_s3_delegated"


@dataclass(kw_only=True)
class IcebergRESTCatalogBasicAuthS3DelegatedDTO(IcebergRESTCatalogS3DelegatedConnectionBaseDTO):
    rest_catalog_username: str
    rest_catalog_password: str
    rest_catalog_auth_type: Literal["basic"] = "basic"


@dataclass(kw_only=True)
class IcebergRESTCatalogOAuth2ClientCredentialsS3DelegatedDTO(IcebergRESTCatalogS3DelegatedConnectionBaseDTO):
    rest_catalog_oauth2_client_id: str
    rest_catalog_oauth2_client_secret: str
    rest_catalog_oauth2_scopes: list[str]
    rest_catalog_oauth2_resource: str | None = None
    rest_catalog_oauth2_audience: str | None = None
    rest_catalog_oauth2_token_endpoint: str | None = None
    rest_catalog_auth_type: Literal["oauth2"] = "oauth2"


# TODO: should be refactored
def get_iceberg_rest_catalog_s3_direct_connection_dto(
    **data,
) -> IcebergRESTCatalogBasicAuthS3BasicDTO | IcebergRESTCatalogOAuth2ClientCredentialsS3BasicDTO:
    if "rest_catalog_oauth2_client_id" in data:
        return IcebergRESTCatalogOAuth2ClientCredentialsS3BasicDTO(**data)
    return IcebergRESTCatalogBasicAuthS3BasicDTO(**data)


def get_iceberg_rest_catalog_s3_delegated_connection_dto(
    **data,
) -> IcebergRESTCatalogBasicAuthS3DelegatedDTO | IcebergRESTCatalogOAuth2ClientCredentialsS3DelegatedDTO:
    if "rest_catalog_oauth2_client_id" in data:
        return IcebergRESTCatalogOAuth2ClientCredentialsS3DelegatedDTO(**data)
    return IcebergRESTCatalogBasicAuthS3DelegatedDTO(**data)


def get_iceberg_connection_dto(**data) -> IcebergConnectionBaseDTO:
    if "s3_warehouse_path" in data:
        return get_iceberg_rest_catalog_s3_direct_connection_dto(**data)
    return get_iceberg_rest_catalog_s3_delegated_connection_dto(**data)


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
    bucket_style: Literal["domain", "path"]
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
