# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field

from syncmaster.server.settings.auth.jwt import JWTSettings


class DummyAuthProviderSettings(BaseModel):
    """Settings for DummyAuthProvider.

    Examples
    --------

    .. code-block:: bash

        SYNCMASTER__AUTH__PROVIDER=syncmaster.server.providers.auth.dummy_provider.DummyAuthProvider
        SYNCMASTER__AUTH__ACCESS_KEY__SECRET_KEY=secret
    """

    access_token: JWTSettings = Field(description="Access-token related settings")
