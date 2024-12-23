# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from cryptography.fernet import Fernet
from pydantic import SecretStr

if TYPE_CHECKING:
    from syncmaster.scheduler.settings import SchedulerAppSettings
    from syncmaster.server.settings import ServerAppSettings
    from syncmaster.worker.settings import WorkerAppSettings


def decrypt_auth_data(
    value: str,
    settings: WorkerAppSettings | SchedulerAppSettings | ServerAppSettings,
) -> dict:
    decryptor = Fernet(settings.encryption.secret_key)
    decrypted = decryptor.decrypt(value)
    return json.loads(decrypted)


def _json_default(value):
    if isinstance(value, SecretStr):
        return value.get_secret_value()


def encrypt_auth_data(
    value: dict,
    settings: WorkerAppSettings | SchedulerAppSettings | ServerAppSettings,
) -> str:
    encryptor = Fernet(settings.encryption.secret_key)
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        default=_json_default,
    )
    encrypted = encryptor.encrypt(serialized.encode("utf-8"))
    return encrypted.decode("utf-8")
