# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import glob
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ByteSize, Field, field_validator

from syncmaster.schemas.v1.transformation_types import FILE_METADATA_FILTER


class NameGlobFilter(BaseModel):
    type: Literal["name_glob"]
    value: str

    @field_validator("value", mode="before")
    def _validate_pattern(cls, value: str) -> str:
        if not glob.has_magic(value):
            raise ValueError(f"Invalid glob: {value!r}")

        return value


class NameRegexpFilter(BaseModel):
    type: Literal["name_regexp"]
    value: str

    @field_validator("value", mode="before")
    def _validate_pattern(cls, value: str) -> str:
        try:
            re.compile(value)
        except re.error as e:
            raise ValueError(f"Invalid regexp: {value!r}") from e

        return value


class FileSizeMinFilter(BaseModel):
    type: Literal["file_size_min"]
    value: ByteSize


class FileSizeMaxFilter(BaseModel):
    type: Literal["file_size_max"]
    value: ByteSize


MetadataFilter = NameGlobFilter | NameRegexpFilter | FileSizeMinFilter | FileSizeMaxFilter


class FileMetadataFilter(BaseModel):
    type: FILE_METADATA_FILTER
    filters: list[Annotated[MetadataFilter, Field(discriminator="type")]] = Field(default_factory=list)
