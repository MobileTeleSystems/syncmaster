# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

import jwt

from syncmaster.exceptions.auth import AuthorizationError


def sign_jwt(payload: dict, secret_key: str, security_algorithm: str) -> str:
    return jwt.encode(
        payload,
        secret_key,
        algorithm=security_algorithm,
    )


def decode_jwt(token: str, secret_key: str, security_algorithm: str) -> dict:
    try:
        result = jwt.decode(
            token,
            secret_key,
            algorithms=[security_algorithm],
        )
        if "exp" not in result:
            msg = "Missing expiration time in token"
            raise jwt.ExpiredSignatureError(msg)
    except jwt.PyJWTError as e:
        msg = "Invalid token"
        raise AuthorizationError(msg) from e
    else:
        return result
