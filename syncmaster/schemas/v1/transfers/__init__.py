# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from syncmaster.schemas.v1.connection_types import FILE_CONNECTION_TYPES
from syncmaster.schemas.v1.connections.connection import ReadConnectionSchema
from syncmaster.schemas.v1.page import PageSchema
from syncmaster.schemas.v1.transfers.db import (
    ClickhouseTransferSourceOrTarget,
    HiveTransferSourceOrTarget,
    IcebergRESTCatalogS3TransferSourceOrTarget,
    MSSQLTransferSourceOrTarget,
    MySQLTransferSourceOrTarget,
    OracleTransferSourceOrTarget,
    PostgresTransferSourceOrTarget,
)
from syncmaster.schemas.v1.transfers.file.ftp import (
    CreateFTPTransferSource,
    CreateFTPTransferTarget,
    ReadFTPTransferSource,
    ReadFTPTransferTarget,
)
from syncmaster.schemas.v1.transfers.file.ftps import (
    CreateFTPSTransferSource,
    CreateFTPSTransferTarget,
    ReadFTPSTransferSource,
    ReadFTPSTransferTarget,
)
from syncmaster.schemas.v1.transfers.file.hdfs import (
    CreateHDFSTransferSource,
    CreateHDFSTransferTarget,
    ReadHDFSTransferSource,
    ReadHDFSTransferTarget,
)
from syncmaster.schemas.v1.transfers.file.s3 import (
    CreateS3TransferSource,
    CreateS3TransferTarget,
    ReadS3TransferSource,
    ReadS3TransferTarget,
)
from syncmaster.schemas.v1.transfers.file.samba import (
    CreateSambaTransferSource,
    CreateSambaTransferTarget,
    ReadSambaTransferSource,
    ReadSambaTransferTarget,
)
from syncmaster.schemas.v1.transfers.file.sftp import (
    CreateSFTPTransferSource,
    CreateSFTPTransferTarget,
    ReadSFTPTransferSource,
    ReadSFTPTransferTarget,
)
from syncmaster.schemas.v1.transfers.file.webdav import (
    CreateWebDAVTransferSource,
    CreateWebDAVTransferTarget,
    ReadWebDAVTransferSource,
    ReadWebDAVTransferTarget,
)
from syncmaster.schemas.v1.transfers.resources import Resources
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
    ClickhouseTransferSourceOrTarget
    | HiveTransferSourceOrTarget
    | IcebergRESTCatalogS3TransferSourceOrTarget
    | MSSQLTransferSourceOrTarget
    | MySQLTransferSourceOrTarget
    | OracleTransferSourceOrTarget
    | PostgresTransferSourceOrTarget
    | ReadHDFSTransferSource
    | ReadS3TransferSource
    | ReadSFTPTransferSource
    | ReadFTPTransferSource
    | ReadFTPSTransferSource
    | ReadWebDAVTransferSource
    | ReadSambaTransferSource
)

ReadTransferSchemaTarget = (
    ClickhouseTransferSourceOrTarget
    | HiveTransferSourceOrTarget
    | IcebergRESTCatalogS3TransferSourceOrTarget
    | MSSQLTransferSourceOrTarget
    | MySQLTransferSourceOrTarget
    | OracleTransferSourceOrTarget
    | PostgresTransferSourceOrTarget
    | ReadHDFSTransferTarget
    | ReadS3TransferTarget
    | ReadSFTPTransferTarget
    | ReadFTPTransferTarget
    | ReadFTPSTransferTarget
    | ReadWebDAVTransferTarget
    | ReadSambaTransferTarget
)

CreateTransferSchemaSource = (
    ClickhouseTransferSourceOrTarget
    | HiveTransferSourceOrTarget
    | IcebergRESTCatalogS3TransferSourceOrTarget
    | MSSQLTransferSourceOrTarget
    | MySQLTransferSourceOrTarget
    | OracleTransferSourceOrTarget
    | PostgresTransferSourceOrTarget
    | CreateHDFSTransferSource
    | CreateS3TransferSource
    | CreateSFTPTransferSource
    | CreateFTPTransferSource
    | CreateFTPSTransferSource
    | CreateWebDAVTransferSource
    | CreateSambaTransferSource
)

CreateTransferSchemaTarget = (
    ClickhouseTransferSourceOrTarget
    | HiveTransferSourceOrTarget
    | IcebergRESTCatalogS3TransferSourceOrTarget
    | MSSQLTransferSourceOrTarget
    | MySQLTransferSourceOrTarget
    | OracleTransferSourceOrTarget
    | PostgresTransferSourceOrTarget
    | CreateHDFSTransferTarget
    | CreateS3TransferTarget
    | CreateSFTPTransferTarget
    | CreateFTPTransferTarget
    | CreateFTPSTransferTarget
    | CreateWebDAVTransferTarget
    | CreateSambaTransferTarget
)

TransformationSchema = DataframeRowsFilter | DataframeColumnsFilter | FileMetadataFilter


class CopyTransferSchema(BaseModel):
    new_group_id: int
    new_queue_id: int
    new_source_connection_name: NameConstr | None = None
    new_target_connection_name: NameConstr | None = None
    new_name: NameConstr | None = None
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
        discriminator="type",
    )
    target_params: ReadTransferSchemaTarget = Field(
        discriminator="type",
    )
    strategy_params: FullStrategy | IncrementalStrategy = Field(
        discriminator="type",
    )
    transformations: list[Annotated[TransformationSchema, Field(discriminator="type")]] = Field(
        default_factory=list,
    )
    resources: Resources

    model_config = ConfigDict(from_attributes=True)


class CreateTransferSchema(BaseModel):
    group_id: int = Field(description="Transfer owner group id")
    source_connection_id: int = Field(description="id of the connection that will be the data source")
    target_connection_id: int = Field(description="id of the connection that will be the data receiver")
    name: NameConstr = Field(description="Transfer name")
    description: str = Field(description="Additional description")
    is_scheduled: bool = Field(description="Is the transfer on schedule")
    queue_id: int = Field(description="id of the queue in which the transfer will be performed")
    schedule: str | None = Field(default=None, description="Execution schedule in cron format")
    source_params: CreateTransferSchemaSource = Field(
        discriminator="type",
        description="Data source parameters",
    )
    target_params: CreateTransferSchemaTarget = Field(
        discriminator="type",
        description="Data receiver parameters",
    )
    strategy_params: FullStrategy | IncrementalStrategy = Field(
        discriminator="type",
        description="Incremental or archive download options",
    )
    transformations: list[
        Annotated[TransformationSchema, Field(discriminator="type", description="List of transformations")]
    ] = Field(default_factory=list)
    resources: Resources = Field(
        default_factory=Resources,
        description="Transfer resources",
    )

    @model_validator(mode="before")
    def validate_scheduling(cls, values):
        is_scheduled, schedule = values.get("is_scheduled"), values.get("schedule")
        if is_scheduled and schedule is None:
            # TODO make checking cron string
            raise ValueError("If transfer must be scheduled than set schedule param")
        return values

    @model_validator(mode="after")
    def validate_increment_by(cls, values):
        if not isinstance(values.strategy_params, IncrementalStrategy):
            return values

        source_type = values.source_params.type
        increment_by = values.strategy_params.increment_by

        if source_type in FILE_CONNECTION_TYPES and increment_by not in ("file_modified_since", "file_name"):
            raise ValueError(
                "Field 'increment_by' must be equal to 'file_modified_since' or 'file_name' for file source types",
            )

        return values

    @model_validator(mode="after")
    def validate_strategy(cls, values):

        if values.source_params.type in ("s3", "hdfs") and isinstance(values.strategy_params, IncrementalStrategy):
            raise ValueError("S3 and HDFS sources do not support incremental strategy for now")

        return values


class ReadFullTransferSchema(ReadTransferSchema):
    source_connection: ReadConnectionSchema
    target_connection: ReadConnectionSchema


class TransferPageSchema(PageSchema):
    items: list[ReadTransferSchema]
