# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pathlib import PurePosixPath

from pydantic import BaseModel, Field, validator

from syncmaster.schemas.v1.transfers.file_format import CSV, JSON, JSONLine


def validate_directory_path(path: str) -> PurePosixPath:
    return PurePosixPath(path)


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
    directory_path: PurePosixPath
    file_format: CSV | JSONLine | JSON = Field(..., discriminator="type")

    class Config:
        arbitrary_types_allowed = True

    _validate_dir_path = validator("directory_path", allow_reuse=True, pre=True)(validate_directory_path)


class CreateFileTransferTarget(BaseModel):
    directory_path: PurePosixPath
    file_format: CSV | JSONLine = Field(..., discriminator="type")  # JSON FORMAT IS NOT SUPPORTED AS A TARGET !

    class Config:
        arbitrary_types_allowed = True

    _validate_dir_path = validator("directory_path", allow_reuse=True, pre=True)(validate_directory_path)
