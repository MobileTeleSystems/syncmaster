# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
    file_format: CSV | JSONLine | JSON | Excel | XML | ORC | Parquet = Field(discriminator="type")
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
    file_format: CSV | JSONLine | JSON | Excel | XML | ORC | Parquet = Field(discriminator="type")
    options: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

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
        default="{run_created_at}-{index}.{extension}",
        description="Template for file naming with required placeholders 'index' and 'extension'",
    )
    options: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    FILE_NAME_PATTERN: ClassVar[re.Pattern] = re.compile(r"^[a-zA-Z0-9_.{}-]+$")

    @field_validator("directory_path", mode="before")
    @classmethod
    def _directory_path_is_valid_path(cls, value):
        if not PurePosixPath(value).is_absolute():
            raise ValueError("Directory path must be absolute")
        return value

    @field_validator("file_name_template")
    @classmethod
    def _validate_file_name_template(cls, value: str) -> str:  # noqa: WPS238
        if not cls.FILE_NAME_PATTERN.match(value):
            raise ValueError("Template contains invalid characters. Allowed: letters, numbers, '.', '_', '-', '{', '}'")

        required_keys = {"index", "extension"}
        placeholders = {key for key in required_keys if f"{{{key}}}" in value}

        missing_keys = sorted(required_keys - placeholders)
        if missing_keys:
            missing_keys_str = ", ".join(missing_keys)
            raise ValueError(f"Missing required placeholders: {missing_keys_str}")

        if "{run_id}" not in value and "{run_created_at}" not in value:
            raise ValueError("At least one of placeholders must be present: {run_id} or {run_created_at}")

        try:
            value.format(index="", extension="", run_created_at="", run_id="")
        except KeyError as e:
            raise ValueError(f"Invalid placeholder: {e}")

        return value
