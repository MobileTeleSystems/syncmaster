# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, ConfigDict, Field

from syncmaster.schemas.v1.auth import ReadBasicAuthSchema, ReadS3AuthSchema
from syncmaster.schemas.v1.auth.samba import ReadSambaAuthSchema
from syncmaster.schemas.v1.types import NameConstr

ReadConnectionAuthDataSchema = ReadBasicAuthSchema | ReadS3AuthSchema | ReadSambaAuthSchema


class CreateConnectionBaseSchema(BaseModel):
    group_id: int = Field(description="Connection owner group id")
    name: NameConstr = Field(description="Connection name")
    description: str = Field(description="Additional description")

    model_config = ConfigDict(populate_by_name=True)


class ReadConnectionBaseSchema(BaseModel):
    id: int
    group_id: int
    name: str
    description: str

    model_config = ConfigDict(populate_by_name=True)


class ReadAuthDataSchema(BaseModel):
    auth_data: ReadConnectionAuthDataSchema = Field(discriminator="type", default=...)
