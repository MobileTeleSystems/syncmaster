# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, ImportString, field_validator

if TYPE_CHECKING:
    from syncmaster.server.providers.auth.base_provider import AuthProvider


class AuthSettings(BaseModel):
    """Authorization-related settings.

    Here you can set auth provider class along with its options.

    Examples
    --------

    ```yaml title="config.yml"
    auth:
        provider: syncmaster.server.providers.auth.dummy_provider.DummyAuthProvider
        # other options passed to AuthProviderSettings, e.g. DummyAuthProviderSettings
        access_key:
            secret_key: jwt_secret
    ```
    """

    provider: ImportString = Field(  # type: ignore[assignment]
        default="syncmaster.server.providers.auth.dummy_provider.DummyAuthProvider",
        description="Full name of auth provider class",
        validate_default=True,
    )

    model_config = ConfigDict(extra="allow")

    @field_validator("provider", mode="after")
    @classmethod
    def _validate_provider(cls, value: type) -> "type[AuthProvider]":
        from syncmaster.server.providers.auth.base_provider import AuthProvider  # noqa: PLC0415

        if not issubclass(value, AuthProvider):
            msg = f"Class {value} is not a subclass of {AuthProvider}"
            raise TypeError(msg)
        return value

    # prevent leaking provider secrets
    def __repr_args__(self):
        return [("provider", self.provider)]
