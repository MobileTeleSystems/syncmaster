# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.api.v1.schemas import S3_TYPE
from app.api.v1.transfers.schemas.file.base import (
    CreateFileTransferSource,
    CreateFileTransferTarget,
    ReadFileTransferSource,
    ReadFileTransferTarget,
)


class S3ReadTransferSource(ReadFileTransferSource):
    type: S3_TYPE


class S3ReadTransferTarget(ReadFileTransferTarget):
    type: S3_TYPE


class S3CreateTransferSource(CreateFileTransferSource):
    type: S3_TYPE


class S3CreateTransferTarget(CreateFileTransferTarget):
    type: S3_TYPE
