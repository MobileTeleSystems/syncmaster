# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from syncmaster.schemas.v1.connections.connection import ReadConnectionSchema
from syncmaster.schemas.v1.page import PageSchema
from syncmaster.schemas.v1.transfers.db import (
    HiveReadTransferSourceAndTarget,
    OracleReadTransferSourceAndTarget,
    PostgresReadTransferSourceAndTarget,
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
from syncmaster.schemas.v1.transfers.strategy import FullStrategy, IncrementalStrategy
from syncmaster.schemas.v1.types import NameConstr

ReadTransferSchemaSource = (
    PostgresReadTransferSourceAndTarget
    | HDFSReadTransferSource
    | HiveReadTransferSourceAndTarget
    | OracleReadTransferSourceAndTarget
    | S3ReadTransferSource
)

ReadTransferSchemaTarget = (
    PostgresReadTransferSourceAndTarget
    | HDFSReadTransferTarget
    | HiveReadTransferSourceAndTarget
    | OracleReadTransferSourceAndTarget
    | S3ReadTransferTarget
)

CreateTransferSchemaSource = (
    PostgresReadTransferSourceAndTarget
    | HDFSCreateTransferSource
    | HiveReadTransferSourceAndTarget
    | OracleReadTransferSourceAndTarget
    | S3CreateTransferSource
)

CreateTransferSchemaTarget = (
    PostgresReadTransferSourceAndTarget
    | HDFSCreateTransferTarget
    | HiveReadTransferSourceAndTarget
    | OracleReadTransferSourceAndTarget
    | S3CreateTransferTarget
)

UpdateTransferSchemaSource = (
    PostgresReadTransferSourceAndTarget
    | HDFSReadTransferSource
    | HiveReadTransferSourceAndTarget
    | OracleReadTransferSourceAndTarget
    | S3CreateTransferSource
    | None
)

UpdateTransferSchemaTarget = (
    PostgresReadTransferSourceAndTarget
    | HDFSReadTransferSource
    | HiveReadTransferSourceAndTarget
    | OracleReadTransferSourceAndTarget
    | S3CreateTransferTarget
    | None
)


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

    @model_validator(mode="before")
    def check_owner_id(cls, values):
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


class ReadFullTransferSchema(ReadTransferSchema):
    source_connection: ReadConnectionSchema
    target_connection: ReadConnectionSchema

    class Config:
        from_attributes = True


class TransferPageSchema(PageSchema):
    items: list[ReadTransferSchema]
