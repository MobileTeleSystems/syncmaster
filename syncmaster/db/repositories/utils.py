# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import json

from cryptography.fernet import Fernet
from pydantic import SecretStr

from syncmaster.settings import Settings


def decrypt_auth_data(
    value: str,
    settings: Settings,
) -> dict:
    decryptor = Fernet(settings.CRYPTO_KEY)
    decrypted = decryptor.decrypt(value)
    return json.loads(decrypted)


def _json_default(value):
    if isinstance(value, SecretStr):
        return value.get_secret_value()


def encrypt_auth_data(
    value: dict,
    settings: Settings,
) -> str:
    encryptor = Fernet(settings.CRYPTO_KEY)
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        default=_json_default,
    )
    encrypted = encryptor.encrypt(serialized.encode("utf-8"))
    return encrypted.decode("utf-8")
