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
    "AuthTokenSchema",
    "TokenPayloadSchema",
    "ConnectionCopySchema",
    "ConnectionPageSchema",
    "CreateConnectionSchema",
    "ReadConnectionSchema",
    "UpdateConnectionSchema",
    "AddUserSchema",
    "CreateGroupSchema",
    "GroupPageSchema",
    "ReadGroupSchema",
    "UpdateGroupSchema",
    "CreateQueueSchema",
    "QueuePageSchema",
    "ReadQueueSchema",
    "UpdateQueueSchema",
    "CreateTransferSchema",
    "TransferPageSchema",
    "ReadTransferSchema",
    "ReadFullTransferSchema",
    "CopyTransferSchema",
    "CreateRunSchema",
    "ReadRunSchema",
    "RunPageSchema",
    "ShortRunSchema",
    "FullStrategy",
    "IncrementalStrategy",
    "CSV",
    "JSON",
    "ORC",
    "XML",
    "Excel",
    "JSONLine",
    "Parquet",
    "ReadUserSchema",
    "FullUserSchema",
    "ReadGroupMember",
    "UserPageSchema",
    "UserPageSchemaAsGroupMember",
]
