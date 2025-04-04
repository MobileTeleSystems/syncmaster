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


class FTPReadTransferSource(ReadFileTransferSource):
    type: FTP_TYPE


class FTPReadTransferTarget(ReadFileTransferTarget):
    type: FTP_TYPE


class FTPCreateTransferSource(CreateFileTransferSource):
    type: FTP_TYPE


class FTPCreateTransferTarget(CreateFileTransferTarget):
    type: FTP_TYPE
