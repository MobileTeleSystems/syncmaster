# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field

from syncmaster.server.settings.auth.jwt import JWTSettings


class DummyAuthProviderSettings(BaseModel):
    """Settings for DummyAuthProvider.

    Examples
    --------

    .. code-block:: yaml
        :caption: config.yml

        auth:
            provider: syncmaster.server.providers.auth.dummy_provider.DummyAuthProvider
            access_key:
                secret_key: jwt_secret
    """

    access_token: JWTSettings = Field(description="Access-token related settings")
