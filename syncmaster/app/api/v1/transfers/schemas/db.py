# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from pydantic import BaseModel

from app.api.v1.schemas import HIVE_TYPE, ORACLE_TYPE, POSTGRES_TYPE


class ReadHiveTransferData(BaseModel):
    type: HIVE_TYPE
    table_name: str


class ReadOracleTransferData(BaseModel):
    type: ORACLE_TYPE
    table_name: str


class ReadPostgresTransferData(BaseModel):
    type: POSTGRES_TYPE
    table_name: str
