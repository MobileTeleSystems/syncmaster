# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from syncmaster.schemas.v1.connection_types import SAMBA_TYPE
from syncmaster.schemas.v1.transfers.file.base import (
    FileTransferSource,
    FileTransferTarget,
)


class SambaTransferSource(FileTransferSource):
    type: SAMBA_TYPE


class SambaTransferTarget(FileTransferTarget):
    type: SAMBA_TYPE
