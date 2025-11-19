# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from syncmaster.schemas.v1.connection_types import SFTP_TYPE
from syncmaster.schemas.v1.transfers.file.base import (
    FileTransferSource,
    FileTransferTarget,
)


class SFTPTransferSource(FileTransferSource):
    type: SFTP_TYPE


class SFTPTransferTarget(FileTransferTarget):
    type: SFTP_TYPE
