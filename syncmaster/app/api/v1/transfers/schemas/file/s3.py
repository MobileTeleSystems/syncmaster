# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pathlib import PurePosixPath

from pydantic import BaseModel, Field, validator

from app.api.v1.schemas import S3_TYPE
from app.api.v1.transfers.schemas.file_format import CSV, JSON, JSONLine


def validate_directory_path(path: str) -> PurePosixPath:
    return PurePosixPath(path)


# At the moment the S3ReadTransferSourceParamsSchema and S3ReadTransferTargetParamsSchema
# classes are identical but may change in the future
class S3ReadTransferSourceParamsSchema(BaseModel):
    type: S3_TYPE
    directory_path: str
    file_format: CSV | JSONLine | JSON = Field(..., discriminator="type")


class S3ReadTransferTargetParamsSchema(BaseModel):
    type: S3_TYPE
    directory_path: str
    file_format: CSV | JSONLine | JSON = Field(..., discriminator="type")


# At the moment the S3CreateTransferSourceParamsSchema and S3CreateTransferTargetParamsSchema
# classes are identical but may change in the future
class S3CreateTransferSourceParamsSchema(BaseModel):
    type: S3_TYPE
    directory_path: PurePosixPath
    file_format: CSV | JSONLine = Field(..., discriminator="type")

    class Config:
        arbitrary_types_allowed = True

    _validate_dir_path = validator("directory_path", allow_reuse=True, pre=True)(validate_directory_path)


class S3CreateTransferTargetParamsSchema(BaseModel):
    type: S3_TYPE
    directory_path: PurePosixPath
    file_format: CSV | JSONLine = Field(..., discriminator="type")  # JSON FORMAT IS NOT SUPPORTED AS A TARGET !

    class Config:
        arbitrary_types_allowed = True

    _validate_dir_path = validator("directory_path", allow_reuse=True, pre=True)(validate_directory_path)
