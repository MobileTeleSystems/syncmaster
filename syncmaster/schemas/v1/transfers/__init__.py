# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

from syncmaster.schemas.v1.connections.connection import ReadConnectionSchema
from syncmaster.schemas.v1.page import PageSchema
from syncmaster.schemas.v1.transfers.db import (
    ClickhouseReadTransferSourceAndTarget,
    HiveReadTransferSourceAndTarget,
    MSSQLReadTransferSourceAndTarget,
    MySQLReadTransferSourceAndTarget,
    OracleReadTransferSourceAndTarget,
    PostgresReadTransferSourceAndTarget,
)
from syncmaster.schemas.v1.transfers.file.ftp import (
    FTPCreateTransferSource,
    FTPCreateTransferTarget,
    FTPReadTransferSource,
    FTPReadTransferTarget,
)
from syncmaster.schemas.v1.transfers.file.ftps import (
    FTPSCreateTransferSource,
    FTPSCreateTransferTarget,
    FTPSReadTransferSource,
    FTPSReadTransferTarget,
)
from syncmaster.schemas.v1.transfers.file.hdfs import (
    HDFSCreateTransferSource,
    HDFSCreateTransferTarget,
    HDFSReadTransferSource,
    HDFSReadTransferTarget,
)
from syncmaster.schemas.v1.transfers.file.s3 import (
    S3CreateTransferSource,
    S3CreateTransferTarget,
    S3ReadTransferSource,
    S3ReadTransferTarget,
)
from syncmaster.schemas.v1.transfers.file.samba import (
    SambaCreateTransferSource,
    SambaCreateTransferTarget,
    SambaReadTransferSource,
    SambaReadTransferTarget,
)
from syncmaster.schemas.v1.transfers.file.sftp import (
    SFTPCreateTransferSource,
    SFTPCreateTransferTarget,
    SFTPReadTransferSource,
    SFTPReadTransferTarget,
)
from syncmaster.schemas.v1.transfers.file.webdav import (
    WebDAVCreateTransferSource,
    WebDAVCreateTransferTarget,
    WebDAVReadTransferSource,
    WebDAVReadTransferTarget,
)
from syncmaster.schemas.v1.transfers.strategy import FullStrategy, IncrementalStrategy
from syncmaster.schemas.v1.transfers.transformations.dataframe_columns_filter import (
    DataframeColumnsFilter,
)
from syncmaster.schemas.v1.transfers.transformations.dataframe_rows_filter import (
    DataframeRowsFilter,
)
from syncmaster.schemas.v1.transfers.transformations.file_metadata_filter import (
    FileMetadataFilter,
)
from syncmaster.schemas.v1.types import NameConstr

ReadTransferSchemaSource = (
    PostgresReadTransferSourceAndTarget
    | HDFSReadTransferSource
    | HiveReadTransferSourceAndTarget
    | OracleReadTransferSourceAndTarget
    | ClickhouseReadTransferSourceAndTarget
    | MSSQLReadTransferSourceAndTarget
    | MySQLReadTransferSourceAndTarget
    | S3ReadTransferSource
    | SFTPReadTransferSource
    | FTPReadTransferSource
    | FTPSReadTransferSource
    | WebDAVReadTransferSource
    | SambaReadTransferSource
)

ReadTransferSchemaTarget = (
    PostgresReadTransferSourceAndTarget
    | HDFSReadTransferTarget
    | HiveReadTransferSourceAndTarget
    | OracleReadTransferSourceAndTarget
    | ClickhouseReadTransferSourceAndTarget
    | MSSQLReadTransferSourceAndTarget
    | MySQLReadTransferSourceAndTarget
    | S3ReadTransferTarget
    | SFTPReadTransferTarget
    | FTPReadTransferTarget
    | FTPSReadTransferTarget
    | WebDAVReadTransferTarget
    | SambaReadTransferTarget
)

CreateTransferSchemaSource = (
    PostgresReadTransferSourceAndTarget
    | HDFSCreateTransferSource
    | HiveReadTransferSourceAndTarget
    | OracleReadTransferSourceAndTarget
    | ClickhouseReadTransferSourceAndTarget
    | MSSQLReadTransferSourceAndTarget
    | MySQLReadTransferSourceAndTarget
    | S3CreateTransferSource
    | SFTPCreateTransferSource
    | FTPCreateTransferSource
    | FTPSCreateTransferSource
    | WebDAVCreateTransferSource
    | SambaCreateTransferSource
)

CreateTransferSchemaTarget = (
    PostgresReadTransferSourceAndTarget
    | HDFSCreateTransferTarget
    | HiveReadTransferSourceAndTarget
    | OracleReadTransferSourceAndTarget
    | ClickhouseReadTransferSourceAndTarget
    | MSSQLReadTransferSourceAndTarget
    | MySQLReadTransferSourceAndTarget
    | S3CreateTransferTarget
    | SFTPCreateTransferTarget
    | FTPCreateTransferTarget
    | FTPSCreateTransferTarget
    | WebDAVCreateTransferTarget
    | SambaCreateTransferTarget
)

UpdateTransferSchemaSource = (
    PostgresReadTransferSourceAndTarget
    | HDFSReadTransferSource
    | HiveReadTransferSourceAndTarget
    | OracleReadTransferSourceAndTarget
    | ClickhouseReadTransferSourceAndTarget
    | MSSQLReadTransferSourceAndTarget
    | MySQLReadTransferSourceAndTarget
    | S3ReadTransferSource
    | SFTPReadTransferSource
    | FTPReadTransferSource
    | FTPSReadTransferSource
    | WebDAVReadTransferSource
    | SambaReadTransferSource
    | None
)

UpdateTransferSchemaTarget = (
    PostgresReadTransferSourceAndTarget
    | HDFSReadTransferSource
    | HiveReadTransferSourceAndTarget
    | OracleReadTransferSourceAndTarget
    | ClickhouseReadTransferSourceAndTarget
    | MSSQLReadTransferSourceAndTarget
    | MySQLReadTransferSourceAndTarget
    | S3ReadTransferTarget
    | SFTPReadTransferTarget
    | FTPReadTransferTarget
    | FTPSReadTransferTarget
    | WebDAVReadTransferTarget
    | SambaReadTransferTarget
    | None
)

TransformationSchema = DataframeRowsFilter | DataframeColumnsFilter | FileMetadataFilter


class CopyTransferSchema(BaseModel):
    new_group_id: int
    new_queue_id: int
    new_source_connection_name: NameConstr | None = None  # noqa: F722
    new_target_connection_name: NameConstr | None = None  # noqa: F722
    new_name: NameConstr | None = None  # noqa: F722
    remove_source: bool = False


class ReadTransferSchema(BaseModel):
    id: int
    group_id: int
    source_connection_id: int
    target_connection_id: int
    name: str
    description: str
    is_scheduled: bool
    schedule: str
    queue_id: int
    source_params: ReadTransferSchemaSource = Field(
        ...,
        discriminator="type",
    )
    target_params: ReadTransferSchemaTarget = Field(
        ...,
        discriminator="type",
    )
    strategy_params: FullStrategy | IncrementalStrategy = Field(
        ...,
        discriminator="type",
    )
    transformations: list[Annotated[TransformationSchema, Field(..., discriminator="type")]] = Field(
        default_factory=list,
    )

    class Config:
        from_attributes = True


class CreateTransferSchema(BaseModel):
    group_id: int = Field(..., description="Transfer owner group id")
    source_connection_id: int = Field(..., description="id of the connection that will be the data source")
    target_connection_id: int = Field(..., description="id of the connection that will be the data receiver")
    name: NameConstr = Field(..., description="Transfer name")  # noqa: F722
    description: str = Field(..., description="Additional description")
    is_scheduled: bool = Field(..., description="Is the transfer on schedule")
    queue_id: int = Field(..., description="id of the queue in which the transfer will be performed")
    schedule: str | None = Field(None, description="Execution schedule in cron format")
    source_params: CreateTransferSchemaSource = Field(
        ...,
        discriminator="type",
        description="Data source parameters",
    )
    target_params: CreateTransferSchemaTarget = Field(
        ...,
        discriminator="type",
        description="Data receiver parameters",
    )
    strategy_params: FullStrategy | IncrementalStrategy = Field(
        ...,
        discriminator="type",
        description="Incremental or archive download options",
    )
    transformations: list[
        Annotated[TransformationSchema, Field(None, discriminator="type", description="List of transformations")]
    ] = Field(default_factory=list)

    @model_validator(mode="before")
    def validate_scheduling(cls, values):
        is_scheduled, schedule = values.get("is_scheduled"), values.get("schedule")
        if is_scheduled and schedule is None:
            # TODO make checking cron string
            raise ValueError("If transfer must be scheduled than set schedule param")
        return values


class UpdateTransferSchema(BaseModel):
    source_connection_id: int | None = None
    target_connection_id: int | None = None
    name: NameConstr | None = None  # noqa: F722
    description: str | None = None
    is_scheduled: bool | None = None
    schedule: str | None = None
    new_queue_id: int | None = None
    source_params: UpdateTransferSchemaSource = Field(discriminator="type", default=None)
    target_params: UpdateTransferSchemaTarget = Field(discriminator="type", default=None)
    strategy_params: FullStrategy | IncrementalStrategy | None = Field(discriminator="type", default=None)
    transformations: list[Annotated[TransformationSchema, Field(discriminator="type", default=None)]] = None


class ReadFullTransferSchema(ReadTransferSchema):
    source_connection: ReadConnectionSchema
    target_connection: ReadConnectionSchema

    class Config:
        from_attributes = True


class TransferPageSchema(PageSchema):
    items: list[ReadTransferSchema]
