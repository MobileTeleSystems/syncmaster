# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field, ImportString


class AuthSettings(BaseModel):
    """Authorization-related settings.

    Here you can set auth provider class.

    Examples
    --------

    .. code-block:: bash

        SYNCMASTER__AUTH__PROVIDER=syncmaster.server.providers.auth.dummy_provider.DummyAuthProvider
    """

    provider: ImportString = Field(  # type: ignore[assignment]
        default="syncmaster.server.providers.auth.dummy_provider.DummyAuthProvider",
        description="Full name of auth provider class",
        validate_default=True,
    )

    class Config:
        extra = "allow"
