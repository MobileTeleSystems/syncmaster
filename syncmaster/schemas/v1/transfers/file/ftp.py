# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from syncmaster.schemas.v1.connection_types import FTP_TYPE
from syncmaster.schemas.v1.transfers.file.base import (
    FileTransferSource,
    FileTransferTarget,
)


class FTPTransferSource(FileTransferSource):
    type: FTP_TYPE


class FTPTransferTarget(FileTransferTarget):
    type: FTP_TYPE
