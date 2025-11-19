# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from syncmaster.schemas.v1.connection_types import FTPS_TYPE
from syncmaster.schemas.v1.transfers.file.base import (
    FileTransferSource,
    FileTransferTarget,
)


class FTPSTransferSource(FileTransferSource):
    type: FTPS_TYPE


class FTPSTransferTarget(FileTransferTarget):
    type: FTPS_TYPE
