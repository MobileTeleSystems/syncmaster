# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from syncmaster.schemas.v1.connection_types import S3_TYPE
from syncmaster.schemas.v1.transfers.file.base import (
    CreateFileTransferSource,
    CreateFileTransferTarget,
    ReadFileTransferSource,
    ReadFileTransferTarget,
)


class ReadS3TransferSource(ReadFileTransferSource):
    type: S3_TYPE


class ReadS3TransferTarget(ReadFileTransferTarget):
    type: S3_TYPE


class CreateS3TransferSource(CreateFileTransferSource):
    type: S3_TYPE


class CreateS3TransferTarget(CreateFileTransferTarget):
    type: S3_TYPE
