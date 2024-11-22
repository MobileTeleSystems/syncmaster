# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import json

from cryptography.fernet import Fernet
from pydantic import SecretStr

from syncmaster.backend.settings import ServerAppSettings as Settings


def decrypt_auth_data(
    value: str,
    settings: Settings,
) -> dict:
    decryptor = Fernet(settings.encryption.crypto_key)
    decrypted = decryptor.decrypt(value)
    return json.loads(decrypted)


def _json_default(value):
    if isinstance(value, SecretStr):
        return value.get_secret_value()


def encrypt_auth_data(
    value: dict,
    settings: Settings,
) -> str:
    encryptor = Fernet(settings.encryption.crypto_key)
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        default=_json_default,
    )
    encrypted = encryptor.encrypt(serialized.encode("utf-8"))
    return encrypted.decode("utf-8")
