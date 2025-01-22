# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from syncmaster.schemas.v1.connection_types import WEBDAV_TYPE
from syncmaster.schemas.v1.transfers.file.base import (
    CreateFileTransferSource,
    CreateFileTransferTarget,
    ReadFileTransferSource,
    ReadFileTransferTarget,
)


class WebDAVReadTransferSource(ReadFileTransferSource):
    type: WEBDAV_TYPE


class WebDAVReadTransferTarget(ReadFileTransferTarget):
    type: WEBDAV_TYPE


class WebDAVCreateTransferSource(CreateFileTransferSource):
    type: WEBDAV_TYPE


class WebDAVCreateTransferTarget(CreateFileTransferTarget):
    type: WEBDAV_TYPE
