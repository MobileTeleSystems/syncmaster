# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated

from pydantic import Field

from syncmaster.schemas.v1.transfers.transformations.dataframe_columns_filter import (
    DataframeColumnsFilter,
)
from syncmaster.schemas.v1.transfers.transformations.dataframe_rows_filter import (
    DataframeRowsFilter,
)
from syncmaster.schemas.v1.transfers.transformations.file_metadata_filter import (
    FileMetadataFilter,
)

TransformationSchema = Annotated[
    DataframeRowsFilter | DataframeColumnsFilter | FileMetadataFilter,
    Field(discriminator="type"),
]

__all__ = [
    "TransformationSchema",
]
