# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from syncmaster.schemas.v1.connection_types import FTP_TYPE
from syncmaster.schemas.v1.transfers.file.base import (
    CreateFileTransferSource,
    CreateFileTransferTarget,
    ReadFileTransferSource,
    ReadFileTransferTarget,
)


class ReadFTPTransferSource(ReadFileTransferSource):
    type: FTP_TYPE


class ReadFTPTransferTarget(ReadFileTransferTarget):
    type: FTP_TYPE


class CreateFTPTransferSource(CreateFileTransferSource):
    type: FTP_TYPE


class CreateFTPTransferTarget(CreateFileTransferTarget):
    type: FTP_TYPE
