# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from syncmaster.schemas.v1.auth import AuthTokenSchema, TokenPayloadSchema
from syncmaster.schemas.v1.connections import (
    ConnectionCopySchema,
    ConnectionPageSchema,
    CreateConnectionSchema,
    ReadConnectionSchema,
    UpdateConnectionSchema,
)
from syncmaster.schemas.v1.groups import (
    AddUserSchema,
    CreateGroupSchema,
    GroupPageSchema,
    ReadGroupSchema,
    UpdateGroupSchema,
)
from syncmaster.schemas.v1.queue import (
    CreateQueueSchema,
    QueuePageSchema,
    ReadQueueSchema,
    UpdateQueueSchema,
)
from syncmaster.schemas.v1.transfers import (
    CopyTransferSchema,
    CreateTransferSchema,
    ReadFullTransferSchema,
    ReadTransferSchema,
    TransferPageSchema,
)
from syncmaster.schemas.v1.transfers.file_format import (
    CSV,
    JSON,
    ORC,
    XML,
    Excel,
    JSONLine,
    Parquet,
)
from syncmaster.schemas.v1.transfers.run import (
    CreateRunSchema,
    ReadRunSchema,
    RunPageSchema,
    ShortRunSchema,
)
from syncmaster.schemas.v1.transfers.strategy import FullStrategy, IncrementalStrategy
from syncmaster.schemas.v1.users import (
    FullUserSchema,
    ReadGroupMember,
    ReadUserSchema,
    UserPageSchema,
    UserPageSchemaAsGroupMember,
)

__all__ = [
    "CSV",
    "JSON",
    "ORC",
    "XML",
    "AddUserSchema",
    "AuthTokenSchema",
    "ConnectionCopySchema",
    "ConnectionPageSchema",
    "CopyTransferSchema",
    "CreateConnectionSchema",
    "CreateGroupSchema",
    "CreateQueueSchema",
    "CreateRunSchema",
    "CreateTransferSchema",
    "Excel",
    "FullStrategy",
    "FullUserSchema",
    "GroupPageSchema",
    "IncrementalStrategy",
    "JSONLine",
    "Parquet",
    "QueuePageSchema",
    "ReadConnectionSchema",
    "ReadFullTransferSchema",
    "ReadGroupMember",
    "ReadGroupSchema",
    "ReadQueueSchema",
    "ReadRunSchema",
    "ReadTransferSchema",
    "ReadUserSchema",
    "RunPageSchema",
    "ShortRunSchema",
    "TokenPayloadSchema",
    "TransferPageSchema",
    "UpdateConnectionSchema",
    "UpdateGroupSchema",
    "UpdateQueueSchema",
    "UserPageSchema",
    "UserPageSchemaAsGroupMember",
]
