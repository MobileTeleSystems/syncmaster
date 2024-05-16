# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field, SecretStr

from syncmaster.schemas.v1.connection_types import POSTGRES_TYPE


class PostgresBaseSchema(BaseModel):
    type: POSTGRES_TYPE

    class Config:
        from_attributes = True


class ReadPostgresConnectionSchema(PostgresBaseSchema):
    host: str
    port: int = Field(gt=0, le=65535)
    database_name: str
    additional_params: dict = Field(default_factory=dict)


class ReadPostgresAuthSchema(PostgresBaseSchema):
    user: str


class UpdatePostgresConnectionSchema(PostgresBaseSchema):
    host: str | None = None
    port: int | None = None
    database_name: str | None = None
    additional_params: dict | None = Field(default_factory=dict)


class UpdatePostgresAuthSchema(PostgresBaseSchema):
    user: str | None = None
    password: SecretStr | None = None


class CreatePostgresConnectionSchema(PostgresBaseSchema):
    host: str
    port: int
    database_name: str
    additional_params: dict = Field(default_factory=dict)


class CreatePostgresAuthSchema(PostgresBaseSchema):
    user: str
    password: SecretStr
