# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0

from schemas.v1.transfers.db import (
    HiveReadTransferSourceAndTarget,
    OracleReadTransferSourceAndTarget,
    PostgresReadTransferSourceAndTarget,
    ReadDBTransfer,
)
from schemas.v1.transfers.file_format import CSV, JSON, JSONLine
from schemas.v1.transfers.run import (
    CreateRunSchema,
    ReadRunSchema,
    RunPageSchema,
    ShortRunSchema,
)
from schemas.v1.transfers.strategy import FullStrategy, IncrementalStrategy
from schemas.v1.transfers.transfer import (
    CopyTransferSchema,
    CreateTransferSchema,
    ReadFullTransferSchema,
    ReadTransferSchema,
    TransferPageSchema,
    UpdateTransferSchema,
)
