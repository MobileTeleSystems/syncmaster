# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.api.v1.schemas import HDFS_TYPE
from app.api.v1.transfers.schemas.file.base import (
    CreateFileTransferSource,
    CreateFileTransferTarget,
    ReadFileTransferSource,
    ReadFileTransferTarget,
)


class HDFSReadTransferSource(ReadFileTransferSource):
    type: HDFS_TYPE


class HDFSReadTransferTarget(ReadFileTransferTarget):
    type: HDFS_TYPE


class HDFSCreateTransferSource(CreateFileTransferSource):
    type: HDFS_TYPE


class HDFSCreateTransferTarget(CreateFileTransferTarget):
    type: HDFS_TYPE
