from pydantic import BaseModel, Field, root_validator

from app.api.v1.schemas import (
    FULL_TYPE,
    INCREMENTAL_TYPE,
    ORACLE_TYPE,
    POSTGRES_TYPE,
    PageSchema,
)


class FullStrategy(BaseModel):
    type: FULL_TYPE


class IncrementalStrategy(BaseModel):
    type: INCREMENTAL_TYPE


class ReadPostgresTransferData(BaseModel):
    type: POSTGRES_TYPE
    table_name: str


class ReadOracleTransferData(BaseModel):
    type: ORACLE_TYPE
    table_name: str


class ReadTransferSchema(BaseModel):
    id: int
    user_id: int | None = None
    group_id: int | None = None
    source_connection_id: int
    target_connection_id: int
    name: str
    description: str
    is_scheduled: bool
    schedule: str
    source_params: ReadPostgresTransferData | ReadOracleTransferData = Field(
        ...,
        discriminator="type",
    )
    target_params: ReadPostgresTransferData | ReadOracleTransferData = Field(
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


class CreateTransferSchema(BaseModel):
    user_id: int | None
    group_id: int | None
    source_connection_id: int
    target_connection_id: int
    name: str
    description: str
    is_scheduled: bool
    schedule: str | None = None
    source_params: ReadPostgresTransferData | ReadOracleTransferData = Field(
        ...,
        discriminator="type",
    )
    target_params: ReadPostgresTransferData | ReadOracleTransferData = Field(
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
    name: str | None
    description: str | None
    is_scheduled: bool | None
    schedule: str | None
    source_params: ReadPostgresTransferData | ReadOracleTransferData | None = Field(
        discriminator="type", default=None
    )
    target_params: ReadPostgresTransferData | ReadOracleTransferData | None = Field(
        discriminator="type", default=None
    )
    strategy_params: FullStrategy | IncrementalStrategy | None = Field(
        discriminator="type", default=None
    )
