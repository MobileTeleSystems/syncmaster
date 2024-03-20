# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
import json

from cryptography.fernet import Fernet

from syncmaster.config import Settings


def decrypt_auth_data(
    value: str,
    settings: Settings,
) -> dict:
    f = Fernet(settings.CRYPTO_KEY)
    return json.loads(f.decrypt(value))


def encrypt_auth_data(
    value: dict,
    settings: Settings,
) -> str:
    key = str.encode(settings.CRYPTO_KEY)
    f = Fernet(key)
    token = f.encrypt(str.encode(json.dumps(value)))
    return token.decode(encoding="utf-8")
