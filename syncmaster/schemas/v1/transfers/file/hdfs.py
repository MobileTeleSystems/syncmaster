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


class ReadHDFSTransferSource(ReadFileTransferSource):
    type: HDFS_TYPE


class ReadHDFSTransferTarget(ReadFileTransferTarget):
    type: HDFS_TYPE


class CreateHDFSTransferSource(CreateFileTransferSource):
    type: HDFS_TYPE


class CreateHDFSTransferTarget(CreateFileTransferTarget):
    type: HDFS_TYPE
