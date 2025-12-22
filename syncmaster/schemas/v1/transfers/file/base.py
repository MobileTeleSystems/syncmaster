# SPDX-FileCopyrightText: 2023-present MTS PJSC
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

# JSON format is not supported for writing
TARGET_FILE_FORMAT = CSV | JSONLine | Excel | XML | ORC | Parquet
SOURCE_FILE_FORMAT = TARGET_FILE_FORMAT | JSON


# At the moment the CreateTransferSourceParams and CreateTransferTargetParams
# classes are identical but may change in the future
class FileTransferSource(BaseModel):
    directory_path: str = Field(
        description="Absolute path to directory",
        json_schema_extra={"pattern": r"^/[\w\d ]+(/[\w\d ]+)*$"},
    )
    file_format: SOURCE_FILE_FORMAT = Field(discriminator="type")
    options: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("directory_path", mode="before")
    @classmethod
    def _directory_path_is_valid_path(cls, value):
        if not PurePosixPath(value).is_absolute():
            raise ValueError("Directory path must be absolute")
        return value


class FileTransferTarget(BaseModel):
    FILE_NAME_PATTERN: ClassVar[str] = r"^[\w.{}-]+$"

    directory_path: str = Field(
        description="Absolute path to directory",
        json_schema_extra={"pattern": r"^/[\w\d ]+(/[\w\d ]+)*$"},
    )
    file_format: TARGET_FILE_FORMAT = Field(discriminator="type")
    file_name_template: str = Field(
        default="{run_created_at}-{index}.{extension}",
        description="Template for file naming with required placeholders 'index' and 'extension'",
        json_schema_extra={"pattern": FILE_NAME_PATTERN},
    )
    options: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("directory_path", mode="before")
    @classmethod
    def _directory_path_is_valid_path(cls, value):
        if not PurePosixPath(value).is_absolute():
            raise ValueError("Directory path must be absolute")
        return value

    @field_validator("file_name_template")
    @classmethod
    def _validate_file_name_template(cls, value: str) -> str:  # noqa: WPS238
        # make error message more user friendly
        if not re.match(cls.FILE_NAME_PATTERN, value):
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
