# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.transformation_types import FILE_METADATA_FILTER


class BaseMetadataFilter(BaseModel):
    value: str


class NameGlobFilter(BaseMetadataFilter):
    type: Literal["name_glob"]


class NameRegexpFilter(BaseMetadataFilter):
    type: Literal["name_regexp"]


class FileSizeMinFilter(BaseMetadataFilter):
    type: Literal["file_size_min"]


class FileSizeMaxFilter(BaseMetadataFilter):
    type: Literal["file_size_max"]


MetadataFilter = NameGlobFilter | NameRegexpFilter | FileSizeMinFilter | FileSizeMaxFilter


class FileMetadataFilter(BaseModel):
    type: FILE_METADATA_FILTER
    filters: list[Annotated[MetadataFilter, Field(..., discriminator="type")]] = Field(default_factory=list)
