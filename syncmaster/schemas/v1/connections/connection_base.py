# SPDX-FileCopyrightText: 2023-2025 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field

from syncmaster.schemas.v1.auth import ReadBasicAuthSchema, ReadS3AuthSchema
from syncmaster.schemas.v1.types import NameConstr

ReadConnectionAuthDataSchema = ReadBasicAuthSchema | ReadS3AuthSchema


class CreateConnectionBaseSchema(BaseModel):
    group_id: int = Field(..., description="Connection owner group id")
    name: NameConstr = Field(..., description="Connection name")  # noqa: F722
    description: str = Field(..., description="Additional description")


class ReadConnectionBaseSchema(BaseModel):
    id: int
    group_id: int
    name: str
    description: str

    class Config:
        from_attributes = True
        populate_by_name = True


class UpdateConnectionBaseSchema(BaseModel):
    name: NameConstr | None = None  # noqa: F722
    description: str | None = None


class ReadAuthDataSchema(BaseModel):
    auth_data: ReadConnectionAuthDataSchema = Field(discriminator="type", default=...)
