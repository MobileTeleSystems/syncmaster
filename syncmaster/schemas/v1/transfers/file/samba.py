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


class SambaReadTransferSource(ReadFileTransferSource):
    type: SAMBA_TYPE


class SambaReadTransferTarget(ReadFileTransferTarget):
    type: SAMBA_TYPE


class SambaCreateTransferSource(CreateFileTransferSource):
    type: SAMBA_TYPE


class SambaCreateTransferTarget(CreateFileTransferTarget):
    type: SAMBA_TYPE
