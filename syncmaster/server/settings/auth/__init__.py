# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, ConfigDict, Field, ImportString


class AuthSettings(BaseModel):
    """Authorization-related settings.

    Here you can set auth provider class along with its options.

    Examples
    --------

    .. code-block:: yaml
        :caption: config.yml

        auth:
            provider: syncmaster.server.providers.auth.dummy_provider.DummyAuthProvider
            # other options passed to AuthProviderSettings, e.g. DummyAuthProviderSettings
            access_key:
                secret_key: jwt_secret
    """

    provider: ImportString = Field(  # type: ignore[assignment]
        default="syncmaster.server.providers.auth.dummy_provider.DummyAuthProvider",
        description="Full name of auth provider class",
        validate_default=True,
    )

    model_config = ConfigDict(extra="allow")
