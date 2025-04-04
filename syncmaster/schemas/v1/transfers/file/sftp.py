# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from syncmaster.schemas.v1.connection_types import SFTP_TYPE
from syncmaster.schemas.v1.transfers.file.base import (
    CreateFileTransferSource,
    CreateFileTransferTarget,
    ReadFileTransferSource,
    ReadFileTransferTarget,
)


class SFTPReadTransferSource(ReadFileTransferSource):
    type: SFTP_TYPE


class SFTPReadTransferTarget(ReadFileTransferTarget):
    type: SFTP_TYPE


class SFTPCreateTransferSource(CreateFileTransferSource):
    type: SFTP_TYPE


class SFTPCreateTransferTarget(CreateFileTransferTarget):
    type: SFTP_TYPE
