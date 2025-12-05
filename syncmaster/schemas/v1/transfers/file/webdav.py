# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from syncmaster.schemas.v1.connection_types import WEBDAV_TYPE
from syncmaster.schemas.v1.transfers.file.base import (
    FileTransferSource,
    FileTransferTarget,
)


class WebDAVTransferSource(FileTransferSource):
    type: WEBDAV_TYPE


class WebDAVTransferTarget(FileTransferTarget):
    type: WEBDAV_TYPE
