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


class ReadSFTPTransferSource(ReadFileTransferSource):
    type: SFTP_TYPE


class ReadSFTPTransferTarget(ReadFileTransferTarget):
    type: SFTP_TYPE


class CreateSFTPTransferSource(CreateFileTransferSource):
    type: SFTP_TYPE


class CreateSFTPTransferTarget(CreateFileTransferTarget):
    type: SFTP_TYPE
