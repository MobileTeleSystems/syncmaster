# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
import time

from jose import JWTError, jwt
from pydantic import ValidationError

from syncmaster.config import Settings
from syncmaster.schemas.v1.auth import TokenPayloadSchema


def sign_jwt(user_id: int, settings: Settings) -> str:
    """This method authentication for dev version without keycloak"""
    payload = {
        "user_id": user_id,
        "expires": time.time() + settings.TOKEN_EXPIRED_TIME,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.SECURITY_ALGORITHM)


def decode_jwt(token: str, settings: Settings) -> TokenPayloadSchema | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.SECURITY_ALGORITHM])
        return TokenPayloadSchema(**payload)
    except (JWTError, ValidationError):
        return None
