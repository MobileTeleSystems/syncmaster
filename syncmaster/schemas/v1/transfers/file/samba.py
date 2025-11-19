# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from syncmaster.schemas.v1.connection_types import SAMBA_TYPE
from syncmaster.schemas.v1.transfers.file.base import (
    CreateFileTransferSource,
    CreateFileTransferTarget,
    ReadFileTransferSource,
    ReadFileTransferTarget,
)


class ReadSambaTransferSource(ReadFileTransferSource):
    type: SAMBA_TYPE


class ReadSambaTransferTarget(ReadFileTransferTarget):
    type: SAMBA_TYPE


class CreateSambaTransferSource(CreateFileTransferSource):
    type: SAMBA_TYPE


class CreateSambaTransferTarget(CreateFileTransferTarget):
    type: SAMBA_TYPE
