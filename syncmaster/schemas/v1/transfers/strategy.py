# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pydantic import BaseModel

from syncmaster.schemas.v1.transfer_types import FULL_TYPE, INCREMENTAL_TYPE


class FullStrategy(BaseModel):
    type: FULL_TYPE


class IncrementalStrategy(BaseModel):
    type: INCREMENTAL_TYPE
