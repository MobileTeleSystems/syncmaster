# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field, ImportString

from syncmaster.backend.settings.auth.jwt import JWTSettings


class AuthSettings(BaseModel):
    """Authorization-related settings.

    Here you can set auth provider class along with its options.

    Examples
    --------

    .. code-block:: bash

        SYNCMASTER__AUTH__PROVIDER=syncmaster.backend.providers.auth.dummy_provider.DummyAuthProvider

        # pass access_key.secret_key = "secret" to DummyAuthProviderSettings
        SYNCMASTER__AUTH__ACCESS_KEY__SECRET_KEY=secret
    """

    provider: ImportString = Field(  # type: ignore[assignment]
        default="syncmaster.backend.providers.auth.dummy.DummyAuthProvider",
        description="Full name of auth provider class",
    )

    class Config:
        extra = "allow"
