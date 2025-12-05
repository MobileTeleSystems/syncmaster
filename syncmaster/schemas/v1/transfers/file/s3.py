# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from syncmaster.schemas.v1.connection_types import S3_TYPE
from syncmaster.schemas.v1.transfers.file.base import (
    FileTransferSource,
    FileTransferTarget,
)


class S3TransferSource(FileTransferSource):
    type: S3_TYPE


class S3TransferTarget(FileTransferTarget):
    type: S3_TYPE
