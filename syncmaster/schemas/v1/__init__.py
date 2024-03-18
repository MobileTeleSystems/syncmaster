# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
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
from syncmaster.schemas.v1.schemas import (
    CSV_FORMAT,
    FULL_TYPE,
    HDFS_TYPE,
    HIVE_TYPE,
    INCREMENTAL_TYPE,
    JSON_FORMAT,
    JSONLINE_FORMAT,
    ORACLE_TYPE,
    POSTGRES_TYPE,
    S3_TYPE,
    MetaPageSchema,
    NameConstr,
    PageSchema,
    StatusCopyTransferResponseSchema,
    StatusResponseSchema,
)
from syncmaster.schemas.v1.transfers import (
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
from syncmaster.schemas.v1.users import (
    FullUserSchema,
    ReadGroupMember,
    ReadUserSchema,
    UpdateUserSchema,
    UserPageSchema,
    UserPageSchemaAsGroupMember,
)
