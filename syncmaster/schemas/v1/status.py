# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel


class StatusResponseSchema(BaseModel):
    ok: bool
    status_code: int
    message: str


class StatusCopyTransferResponseSchema(StatusResponseSchema):
    source_connection_id: int
    target_connection_id: int
    copied_transfer_id: int
