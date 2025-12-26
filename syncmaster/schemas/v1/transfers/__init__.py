# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
)

from syncmaster.schemas.v1.connection_types import FILE_CONNECTION_TYPES
from syncmaster.schemas.v1.connections import ReadConnectionSchema
from syncmaster.schemas.v1.page import PageSchema
from syncmaster.schemas.v1.transfers.db import DBTransferSourceOrTarget
from syncmaster.schemas.v1.transfers.file import FileTransferSource, FileTransferTarget
from syncmaster.schemas.v1.transfers.resources import Resources
from syncmaster.schemas.v1.transfers.strategy import (
    FullStrategy,
    IncrementalStrategy,
    Strategy,
)
from syncmaster.schemas.v1.transfers.transformations import TransformationSchema
from syncmaster.schemas.v1.types import NameConstr

TransferSchemaSource = Annotated[DBTransferSourceOrTarget | FileTransferSource, Field(discriminator="type")]
TransferSchemaTarget = Annotated[DBTransferSourceOrTarget | FileTransferTarget, Field(discriminator="type")]


class TransferSchema(BaseModel):
    group_id: int = Field(description="Transfer owner group id")
    queue_id: int = Field(description="id of the queue in which the transfer will be performed")
    source_connection_id: int = Field(description="id of the connection that will be the data source")
    target_connection_id: int = Field(description="id of the connection that will be the data receiver")
    name: NameConstr = Field(description="Transfer name")
    description: str = Field(default="", description="Human-readable description")
    source_params: TransferSchemaSource = Field(description="Data source parameters")
    target_params: TransferSchemaTarget = Field(description="Data target parameters")
    strategy_params: Strategy = Field(default_factory=FullStrategy, description="Incremental of full strategy")
    transformations: list[TransformationSchema] = Field(default_factory=list, description="List of transformations")
    resources: Resources = Field(default_factory=Resources, description="Transfer resources")
    is_scheduled: bool = Field(default=False, description="Is the transfer on schedule")
    schedule: str | None = Field(
        default=None,
        description="Execution schedule in cron format",
        validate_default=True,
    )


class CreateTransferSchema(TransferSchema):
    @field_validator("schedule", mode="after")
    @classmethod
    def validate_scheduling(cls, value: str | None, info: ValidationInfo):
        if not value and info.data.get("is_scheduled"):
            # TODO make checking cron string
            msg = "If transfer must be scheduled then set schedule"
            raise ValueError(msg)
        return value or None

    @field_validator("strategy_params", mode="after")
    @classmethod
    def validate_strategy(cls, value: Strategy, info: ValidationInfo):
        if isinstance(value, IncrementalStrategy):
            if info.data["source_params"].type in ("s3", "hdfs"):
                msg = "S3 and HDFS sources do not support incremental strategy for now"
                raise ValueError(msg)

            source_type = info.data["source_params"].type
            if source_type in FILE_CONNECTION_TYPES and value.increment_by not in (
                "file_modified_since",
                "file_name",
            ):
                msg = "Field 'increment_by' must be equal to 'file_modified_since' or 'file_name' for file source types"
                raise ValueError(msg)
        return value


class ReadTransferSchema(TransferSchema):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ReadFullTransferSchema(ReadTransferSchema):
    source_connection: ReadConnectionSchema
    target_connection: ReadConnectionSchema


class TransferPageSchema(PageSchema):
    items: list[ReadTransferSchema]


class CopyTransferSchema(BaseModel):
    new_group_id: int = Field(description="New group id")
    new_queue_id: int = Field(description="New queue id")
    new_source_connection_name: NameConstr | None = Field(default=None, description="New source connection name")
    new_target_connection_name: NameConstr | None = Field(default=None, description="New target connection name")
    new_name: NameConstr | None = Field(default=None, description="New name")
    remove_source: bool = Field(default=False, description="Set `true` to move transfer instead of copying")
