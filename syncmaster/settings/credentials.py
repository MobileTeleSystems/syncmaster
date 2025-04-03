# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import textwrap

from pydantic import BaseModel, Field


class CredentialsEncryptionSettings(BaseModel):
    """Settings for encrypting & decrypting credential data stored in database.

    Connecting to source and target databases, file systems and so on requires credentials to be passed.
    For now, SyncMaster stores all credentials in database table ``credentials``, in encrypted form.
    This is done by symmetric algorithm `Fernet <https://cryptography.io/en/latest/fernet/>`_.

    Before starting SyncMaster, generate a new key using the following example:

    >>> from cryptography.fernet import Fernet
    >>> Fernet.generate_key().decode('utf-8')
    UBgPTioFrtH2unlC4XFDiGf5sYfzbdSf_VgiUSaQc94=

    Examples
    --------

    .. code-block:: bash

        # Set the encryption key
        SYNCMASTER__ENCRYPTION__SECRET_KEY=secret_key
    """

    secret_key: str = Field(
        description=textwrap.dedent(
            "Secret key for encrypting/decrypting credentials stored in database.",
        ),
    )
