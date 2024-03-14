# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0

from schemas.v1.auth import AuthTokenSchema, TokenPayloadSchema
from schemas.v1.connections import (
    ConnectionCopySchema,
    ConnectionPageSchema,
    CreateConnectionSchema,
    ReadConnectionSchema,
    UpdateConnectionSchema,
)
from schemas.v1.groups import (
    AddUserSchema,
    CreateGroupSchema,
    GroupPageSchema,
    ReadGroupSchema,
    UpdateGroupSchema,
)
from schemas.v1.queue import (
    CreateQueueSchema,
    QueuePageSchema,
    ReadQueueSchema,
    UpdateQueueSchema,
)
from schemas.v1.schemas import (
    MetaPageSchema,
    PageSchema,
    StatusCopyTransferResponseSchema,
    StatusResponseSchema,
)
from schemas.v1.transfers import (
    CSV,
    JSON,
    CopyTransferSchema,
    CreateRunSchema,
    CreateTransferSchema,
    FullStrategy,
    HiveReadTransferSourceAndTarget,
    IncrementalStrategy,
    JSONLine,
    OracleReadTransferSourceAndTarget,
    PostgresReadTransferSourceAndTarget,
    ReadDBTransfer,
    ReadFullTransferSchema,
    ReadRunSchema,
    ReadTransferSchema,
    RunPageSchema,
    ShortRunSchema,
    TransferPageSchema,
    UpdateTransferSchema,
)
from schemas.v1.users import (
    FullUserSchema,
    ReadGroupMember,
    ReadUserSchema,
    UpdateUserSchema,
    UserPageSchema,
    UserPageSchemaAsGroupMember,
)
