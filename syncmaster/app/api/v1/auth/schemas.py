# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel


class TokenPayloadSchema(BaseModel):
    user_id: int


class AuthTokenSchema(BaseModel):
    access_token: str
    refresh_token: str
