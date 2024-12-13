# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.connections.clickhouse import (
    CreateClickhouseConnectionSchema,
    ReadClickhouseConnectionSchema,
    UpdateClickhouseConnectionSchema,
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
from syncmaster.schemas.v1.page import PageSchema
from syncmaster.schemas.v1.types import NameConstr

CreateConnectionSchema = Annotated[
    CreateOracleConnectionSchema
    | CreatePostgresConnectionSchema
    | CreateMySQLConnectionSchema
    | CreateMSSQLConnectionSchema
    | CreateClickhouseConnectionSchema
    | CreateHiveConnectionSchema
    | CreateHDFSConnectionSchema
    | CreateS3ConnectionSchema,
    Field(discriminator="type"),
]
ReadConnectionSchema = Annotated[
    ReadOracleConnectionSchema
    | ReadPostgresConnectionSchema
    | ReadMySQLConnectionSchema
    | ReadMSSQLConnectionSchema
    | ReadClickhouseConnectionSchema
    | ReadHiveConnectionSchema
    | ReadHDFSConnectionSchema
    | ReadS3ConnectionSchema,
    Field(discriminator="type"),
]
UpdateConnectionSchema = Annotated[
    UpdateOracleConnectionSchema
    | UpdatePostgresConnectionSchema
    | UpdateMySQLConnectionSchema
    | UpdateMSSQLConnectionSchema
    | UpdateClickhouseConnectionSchema
    | UpdateHiveConnectionSchema
    | UpdateHDFSConnectionSchema
    | UpdateS3ConnectionSchema,
    Field(discriminator="type"),
]


class ConnectionCopySchema(BaseModel):
    new_group_id: int
    new_name: NameConstr | None = None  # noqa: F722
    remove_source: bool = False


class ConnectionPageSchema(PageSchema):
    items: list[ReadConnectionSchema]
