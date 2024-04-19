# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pathlib import PurePosixPath

from pydantic import BaseModel, Field, field_validator

from syncmaster.schemas.v1.transfers.file_format import CSV, JSON, JSONLine


# At the moment the ReadTransferSourceParams and ReadTransferTargetParams
# classes are identical but may change in the future
class ReadFileTransferSource(BaseModel):
    directory_path: str
    file_format: CSV | JSONLine | JSON = Field(..., discriminator="type")


class ReadFileTransferTarget(BaseModel):
    directory_path: str
    file_format: CSV | JSONLine = Field(..., discriminator="type")  # JSON format is not supported for writing


# At the moment the CreateTransferSourceParams and CreateTransferTargetParams
# classes are identical but may change in the future
class CreateFileTransferSource(BaseModel):
    directory_path: str
    file_format: CSV | JSONLine | JSON = Field(..., discriminator="type")

    class Config:
        arbitrary_types_allowed = True

    @field_validator("directory_path", mode="before")
    @classmethod
    def _directory_path_is_valid_path(cls, value):
        if not PurePosixPath(value).is_absolute():
            raise ValueError("Directory path must be absolute")
        return value


class CreateFileTransferTarget(BaseModel):
    directory_path: str
    file_format: CSV | JSONLine = Field(..., discriminator="type")  # JSON FORMAT IS NOT SUPPORTED AS A TARGET !

    class Config:
        arbitrary_types_allowed = True

    @field_validator("directory_path", mode="before")
    @classmethod
    def _directory_path_is_valid_path(cls, value):
        if not PurePosixPath(value).is_absolute():
            raise ValueError("Directory path must be absolute")
        return value
