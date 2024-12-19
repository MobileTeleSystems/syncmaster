# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from fastapi import Request
from fastapi.security.utils import get_authorization_scheme_param


async def get_access_token(request: Request) -> str | None:
    authorization = request.headers.get("Authorization")
    scheme, token = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        return None
    return token
