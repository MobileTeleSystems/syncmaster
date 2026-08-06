# SPDX-FileCopyrightText: 2025-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from fastapi import Request

from syncmaster.server.providers.auth.base_provider import AuthProvider


async def get_auth_provider(request: Request) -> AuthProvider:
    return request.app.state.auth_provider


async def get_personal_token_provider(request: Request) -> AuthProvider:
    return request.app.state.personal_token_auth_provider
