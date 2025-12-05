# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from syncmaster.schemas.v1.transfers.file.ftp import (
    FTPTransferSource,
    FTPTransferTarget,
)
from syncmaster.schemas.v1.transfers.file.ftps import (
    FTPSTransferSource,
    FTPSTransferTarget,
)
from syncmaster.schemas.v1.transfers.file.hdfs import (
    HDFSTransferSource,
    HDFSTransferTarget,
)
from syncmaster.schemas.v1.transfers.file.s3 import (
    S3TransferSource,
    S3TransferTarget,
)
from syncmaster.schemas.v1.transfers.file.samba import (
    SambaTransferSource,
    SambaTransferTarget,
)
from syncmaster.schemas.v1.transfers.file.sftp import (
    SFTPTransferSource,
    SFTPTransferTarget,
)
from syncmaster.schemas.v1.transfers.file.webdav import (
    WebDAVTransferSource,
    WebDAVTransferTarget,
)

FileTransferSource = (
    HDFSTransferSource
    | S3TransferSource
    | SFTPTransferSource
    | FTPTransferSource
    | FTPSTransferSource
    | WebDAVTransferSource
    | SambaTransferSource
)

FileTransferTarget = (
    HDFSTransferTarget
    | S3TransferTarget
    | SFTPTransferTarget
    | FTPTransferTarget
    | FTPSTransferTarget
    | WebDAVTransferTarget
    | SambaTransferTarget
)

__all__ = [
    "FileTransferSource",
    "FileTransferTarget",
]
