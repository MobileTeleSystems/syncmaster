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


class FTPSReadTransferSource(ReadFileTransferSource):
    type: FTPS_TYPE


class FTPSReadTransferTarget(ReadFileTransferTarget):
    type: FTPS_TYPE


class FTPSCreateTransferSource(CreateFileTransferSource):
    type: FTPS_TYPE


class FTPSCreateTransferTarget(CreateFileTransferTarget):
    type: FTPS_TYPE
