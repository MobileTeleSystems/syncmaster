# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.connections.clickhouse import (
    CreateClickhouseConnectionSchema,
    ReadClickhouseConnectionSchema,
    UpdateClickhouseConnectionSchema,
)
from syncmaster.schemas.v1.connections.ftp import (
    CreateFTPConnectionSchema,
    ReadFTPConnectionSchema,
    UpdateFTPConnectionSchema,
)
from syncmaster.schemas.v1.connections.ftps import (
    CreateFTPSConnectionSchema,
    ReadFTPSConnectionSchema,
    UpdateFTPSConnectionSchema,
)
from syncmaster.schemas.v1.connections.hdfs import (
    CreateHDFSConnectionSchema,
    ReadHDFSConnectionSchema,
    UpdateHDFSConnectionSchema,
)
from syncmaster.schemas.v1.connections.hive import (
    CreateHiveConnectionSchema,
    ReadHiveConnectionSchema,
    UpdateHiveConnectionSchema,
)
from syncmaster.schemas.v1.connections.iceberg import (
    CreateIcebergConnectionSchema,
    ReadIcebergConnectionSchema,
    UpdateIcebergConnectionSchema,
)
from syncmaster.schemas.v1.connections.mssql import (
    CreateMSSQLConnectionSchema,
    ReadMSSQLConnectionSchema,
    UpdateMSSQLConnectionSchema,
)
from syncmaster.schemas.v1.connections.mysql import (
    CreateMySQLConnectionSchema,
    ReadMySQLConnectionSchema,
    UpdateMySQLConnectionSchema,
)
from syncmaster.schemas.v1.connections.oracle import (
    CreateOracleConnectionSchema,
    ReadOracleConnectionSchema,
    UpdateOracleConnectionSchema,
)
from syncmaster.schemas.v1.connections.postgres import (
    CreatePostgresConnectionSchema,
    ReadPostgresConnectionSchema,
    UpdatePostgresConnectionSchema,
)
from syncmaster.schemas.v1.connections.s3 import (
    CreateS3ConnectionSchema,
    ReadS3ConnectionSchema,
    UpdateS3ConnectionSchema,
)
from syncmaster.schemas.v1.connections.samba import (
    CreateSambaConnectionSchema,
    ReadSambaConnectionSchema,
    UpdateSambaConnectionSchema,
)
from syncmaster.schemas.v1.connections.sftp import (
    CreateSFTPConnectionSchema,
    ReadSFTPConnectionSchema,
    UpdateSFTPConnectionSchema,
)
from syncmaster.schemas.v1.connections.webdav import (
    CreateWebDAVConnectionSchema,
    ReadWebDAVConnectionSchema,
    UpdateWebDAVConnectionSchema,
)
from syncmaster.schemas.v1.page import PageSchema
from syncmaster.schemas.v1.types import NameConstr

CreateConnectionSchema = Annotated[
    CreateClickhouseConnectionSchema
    | CreateHiveConnectionSchema
    | CreateIcebergConnectionSchema
    | CreateMSSQLConnectionSchema
    | CreateMySQLConnectionSchema
    | CreateOracleConnectionSchema
    | CreatePostgresConnectionSchema
    | CreateFTPConnectionSchema
    | CreateFTPSConnectionSchema
    | CreateHDFSConnectionSchema
    | CreateS3ConnectionSchema
    | CreateSambaConnectionSchema
    | CreateSFTPConnectionSchema
    | CreateWebDAVConnectionSchema,
    Field(discriminator="type"),
]
ReadConnectionSchema = Annotated[
    ReadClickhouseConnectionSchema
    | ReadHiveConnectionSchema
    | ReadIcebergConnectionSchema
    | ReadMSSQLConnectionSchema
    | ReadMySQLConnectionSchema
    | ReadOracleConnectionSchema
    | ReadPostgresConnectionSchema
    | ReadFTPConnectionSchema
    | ReadFTPSConnectionSchema
    | ReadHDFSConnectionSchema
    | ReadS3ConnectionSchema
    | ReadSambaConnectionSchema
    | ReadSFTPConnectionSchema
    | ReadWebDAVConnectionSchema,
    Field(discriminator="type"),
]
UpdateConnectionSchema = Annotated[
    UpdateClickhouseConnectionSchema
    | UpdateHiveConnectionSchema
    | UpdateIcebergConnectionSchema
    | UpdateMSSQLConnectionSchema
    | UpdateMySQLConnectionSchema
    | UpdateOracleConnectionSchema
    | UpdatePostgresConnectionSchema
    | UpdateFTPConnectionSchema
    | UpdateFTPSConnectionSchema
    | UpdateHDFSConnectionSchema
    | UpdateS3ConnectionSchema
    | UpdateSambaConnectionSchema
    | UpdateSFTPConnectionSchema
    | UpdateWebDAVConnectionSchema,
    Field(discriminator="type"),
]


class ConnectionCopySchema(BaseModel):
    new_group_id: int = Field(description="New group id")
    new_name: NameConstr | None = Field(default=None, description="New name")
    remove_source: bool = Field(default=False, description="Set `true` to move connection instead of copying")


class ConnectionPageSchema(PageSchema):
    items: list[ReadConnectionSchema]
