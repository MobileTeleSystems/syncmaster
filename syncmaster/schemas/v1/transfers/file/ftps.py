# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from syncmaster.schemas.v1.connection_types import FTPS_TYPE
from syncmaster.schemas.v1.transfers.file.base import (
    CreateFileTransferSource,
    CreateFileTransferTarget,
    ReadFileTransferSource,
    ReadFileTransferTarget,
)


class ReadFTPSTransferSource(ReadFileTransferSource):
    type: FTPS_TYPE


class ReadFTPSTransferTarget(ReadFileTransferTarget):
    type: FTPS_TYPE


class CreateFTPSTransferSource(CreateFileTransferSource):
    type: FTPS_TYPE


class CreateFTPSTransferTarget(CreateFileTransferTarget):
    type: FTPS_TYPE
