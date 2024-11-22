# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field


class CredentialsEncryptionSettings(BaseModel):
    """Settings for encrypting & decrypting credential data stored in app.

    Examples
    --------

    .. code-block:: bash

        # Set the encryption key
        SYNCMASTER_CRYPTO_KEY=secret_key
    """

    crypto_key: str = Field(description="Key for encrypt/decrypt credentials data")
