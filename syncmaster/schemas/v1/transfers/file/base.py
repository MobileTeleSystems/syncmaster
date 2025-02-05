# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any

from pydantic import BaseModel, Field, field_validator

from syncmaster.schemas.v1.transfers.file_format import (
    CSV,
    JSON,
    ORC,
    XML,
    Excel,
    JSONLine,
    Parquet,
)


# At the moment the ReadTransferSourceParams and ReadTransferTargetParams
# classes are identical but may change in the future
class ReadFileTransferSource(BaseModel):
    directory_path: str
    file_format: CSV | JSONLine | JSON | Excel | XML | ORC | Parquet = Field(..., discriminator="type")
    options: dict[str, Any]


class ReadFileTransferTarget(BaseModel):
    directory_path: str
    # JSON format is not supported for writing
    file_format: CSV | JSONLine | Excel | XML | ORC | Parquet = Field(
        ...,
        discriminator="type",
    )
    file_name_template: str
    options: dict[str, Any]


# At the moment the CreateTransferSourceParams and CreateTransferTargetParams
# classes are identical but may change in the future
class CreateFileTransferSource(BaseModel):
    directory_path: str
    file_format: CSV | JSONLine | JSON | Excel | XML | ORC | Parquet = Field(..., discriminator="type")
    options: dict[str, Any] = Field(default_factory=dict)

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
    # JSON format is not supported as a target
    file_format: CSV | JSONLine | Excel | XML | ORC | Parquet = Field(
        ...,
        discriminator="type",
    )
    file_name_template: str = Field(
        default="{run_created_at}_{index}.{extension}",
        description="Template for file naming with required placeholders 'index' and 'extension'",
    )
    options: dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    @field_validator("directory_path", mode="before")
    @classmethod
    def _directory_path_is_valid_path(cls, value):
        if not PurePosixPath(value).is_absolute():
            raise ValueError("Directory path must be absolute")
        return value

    @field_validator("file_name_template")
    @classmethod
    def validate_file_name_template(cls, value):
        required_keys = {"index", "extension"}
        placeholders = {key for key in required_keys if f"{{{key}}}" in value}

        missing_keys = sorted(required_keys - placeholders)
        if missing_keys:
            raise ValueError(f"Missing required placeholders: {', '.join(missing_keys)}")

        try:
            value.format(index="", extension="", run_created_at="", run_id="")
        except KeyError as e:
            raise ValueError(f"Invalid placeholder: {e}")

        return value
