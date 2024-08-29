# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from syncmaster.schemas.v1.connection_types import HDFS_TYPE
from syncmaster.schemas.v1.transfers.file.base import (
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
