from datetime import datetime

from pydantic import BaseModel, Field, root_validator

from app.api.v1.connections.schemas import ReadConnectionSchema
from app.api.v1.schemas import (
    FULL_TYPE,
    HIVE_TYPE,
    INCREMENTAL_TYPE,
    ORACLE_TYPE,
    POSTGRES_TYPE,
    NameConstr,
    PageSchema,
)
from app.db.models import Status


class FullStrategy(BaseModel):
    type: FULL_TYPE


class IncrementalStrategy(BaseModel):
    type: INCREMENTAL_TYPE


class ReadHiveTransferData(BaseModel):
    type: HIVE_TYPE
    table_name: str


class ReadOracleTransferData(BaseModel):
    type: ORACLE_TYPE
    table_name: str


class ReadPostgresTransferData(BaseModel):
    type: POSTGRES_TYPE
    table_name: str


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
    source_params: ReadPostgresTransferData | ReadOracleTransferData | ReadHiveTransferData = Field(
        ...,
        discriminator="type",
    )
    target_params: ReadPostgresTransferData | ReadOracleTransferData | ReadHiveTransferData = Field(
        ...,
        discriminator="type",
    )
    strategy_params: FullStrategy | IncrementalStrategy = Field(
        ...,
        discriminator="type",
    )

    class Config:
        orm_mode = True


class TransferPageSchema(PageSchema):
    items: list[ReadTransferSchema]


class CopyTransferSchema(BaseModel):
    new_group_id: int
    new_queue_id: int
    new_source_connection_name: NameConstr | None = None  # type: ignore # noqa: F722
    new_target_connection_name: NameConstr | None = None  # type: ignore # noqa: F722
    new_name: NameConstr | None  # type: ignore # noqa: F722
    remove_source: bool = False


class CreateTransferSchema(BaseModel):
    group_id: int
    source_connection_id: int
    target_connection_id: int
    name: NameConstr  # type: ignore # noqa: F722
    description: str
    is_scheduled: bool
    queue_id: int
    schedule: str | None = None
    source_params: ReadPostgresTransferData | ReadOracleTransferData | ReadHiveTransferData = Field(
        ...,
        discriminator="type",
    )
    target_params: ReadPostgresTransferData | ReadOracleTransferData | ReadHiveTransferData = Field(
        ...,
        discriminator="type",
    )
    strategy_params: FullStrategy | IncrementalStrategy = Field(
        ...,
        discriminator="type",
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
    source_params: ReadPostgresTransferData | ReadOracleTransferData | ReadHiveTransferData | None = Field(
        discriminator="type", default=None
    )
    target_params: ReadPostgresTransferData | ReadOracleTransferData | ReadHiveTransferData | None = Field(
        discriminator="type", default=None
    )
    strategy_params: FullStrategy | IncrementalStrategy | None = Field(discriminator="type", default=None)


class ShortRunSchema(BaseModel):
    id: int
    transfer_id: int
    started_at: datetime | None
    ended_at: datetime | None
    status: Status
    log_url: str | None

    class Config:
        orm_mode = True


class RunPageSchema(PageSchema):
    items: list[ShortRunSchema]


class ReadRunSchema(ShortRunSchema):
    transfer_dump: dict

    class Config:
        orm_mode = True


class ReadFullTransferSchema(ReadTransferSchema):
    source_connection: ReadConnectionSchema
    target_connection: ReadConnectionSchema

    class Config:
        orm_mode = True
