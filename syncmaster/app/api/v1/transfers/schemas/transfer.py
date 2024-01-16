# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pydantic import BaseModel, Field, root_validator

from app.api.v1.connections.schemas import ReadConnectionSchema
from app.api.v1.schemas import NameConstr, PageSchema
from app.api.v1.transfers.schemas.db import (
    ReadHiveTransferData,
    ReadOracleTransferData,
    ReadPostgresTransferData,
)
from app.api.v1.transfers.schemas.file.s3 import (
    S3CreateTransferSourceParamsSchema,
    S3CreateTransferTargetParamsSchema,
    S3ReadTransferSourceParamsSchema,
    S3ReadTransferTargetParamsSchema,
)
from app.api.v1.transfers.schemas.strategy import FullStrategy, IncrementalStrategy


class CopyTransferSchema(BaseModel):
    new_group_id: int
    new_queue_id: int
    new_source_connection_name: NameConstr | None = None  # type: ignore # noqa: F722
    new_target_connection_name: NameConstr | None = None  # type: ignore # noqa: F722
    new_name: NameConstr | None  # type: ignore # noqa: F722
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
    source_params: (
        ReadPostgresTransferData | ReadOracleTransferData | ReadHiveTransferData | S3ReadTransferSourceParamsSchema
    ) = Field(
        ...,
        discriminator="type",
    )
    target_params: (
        ReadPostgresTransferData | ReadOracleTransferData | ReadHiveTransferData | S3ReadTransferTargetParamsSchema
    ) = Field(
        ...,
        discriminator="type",
    )
    strategy_params: FullStrategy | IncrementalStrategy = Field(
        ...,
        discriminator="type",
    )

    class Config:
        orm_mode = True


class CreateTransferSchema(BaseModel):
    group_id: int = Field(..., description="Transfer owner group id")
    source_connection_id: int = Field(..., description="id of the connection that will be the data source")
    target_connection_id: int = Field(..., description="id of the connection that will be the data receiver")
    name: NameConstr = Field(..., description="Transfer name")  # type: ignore # noqa: F722
    description: str = Field(..., description="Additional description")
    is_scheduled: bool = Field(..., description="Is the transfer on schedule")
    queue_id: int = Field(..., description="id of the queue in which the transfer will be performed")
    schedule: str | None = Field(None, description="Execution schedule in cron format")
    source_params: (
        ReadPostgresTransferData | ReadOracleTransferData | ReadHiveTransferData | S3CreateTransferSourceParamsSchema
    ) = Field(
        ...,
        discriminator="type",
        description="Data source parameters",
    )
    target_params: (
        ReadPostgresTransferData | ReadOracleTransferData | ReadHiveTransferData | S3CreateTransferTargetParamsSchema
    ) = Field(
        ...,
        discriminator="type",
        description="Data receiver parameters",
    )
    strategy_params: FullStrategy | IncrementalStrategy = Field(
        ...,
        discriminator="type",
        description="Incremental or archive download options",
    )

    @root_validator
    def check_owner_id(cls, values):
        is_scheduled, schedule = values.get("is_scheduled"), values.get("schedule")
        if is_scheduled and schedule is None:
            # TODO make checking cron string
            raise ValueError("If transfer must be scheduled than set schedule param")
        return values


class UpdateTransferSchema(BaseModel):
    source_connection_id: int | None
    target_connection_id: int | None
    name: NameConstr | None  # type: ignore # noqa: F722
    description: str | None
    is_scheduled: bool | None
    schedule: str | None
    new_queue_id: int | None
    source_params: (
        ReadPostgresTransferData
        | ReadOracleTransferData
        | ReadHiveTransferData
        | S3CreateTransferSourceParamsSchema
        | None
    ) = Field(discriminator="type", default=None)
    target_params: (
        ReadPostgresTransferData
        | ReadOracleTransferData
        | ReadHiveTransferData
        | S3CreateTransferTargetParamsSchema
        | None
    ) = Field(discriminator="type", default=None)
    strategy_params: FullStrategy | IncrementalStrategy | None = Field(discriminator="type", default=None)


class ReadFullTransferSchema(ReadTransferSchema):
    source_connection: ReadConnectionSchema
    target_connection: ReadConnectionSchema

    class Config:
        orm_mode = True


class TransferPageSchema(PageSchema):
    items: list[ReadTransferSchema]
