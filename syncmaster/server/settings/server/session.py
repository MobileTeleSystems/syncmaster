# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0


import textwrap

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    ValidationInfo,
    field_validator,
)


class SessionSettings(BaseModel):
    """Session Middleware Settings.

    Required for :ref:`keycloak-auth-provider`.

    See `SessionMiddleware <https://www.starlette.io/middleware/#sessionmiddleware>`_ documentation.

    .. note::

        You can pass here any extra option supported by ``SessionMiddleware``,
        even if it is not mentioned in documentation.

    Examples
    --------

    For development environment:

    .. code-block:: yaml
        :caption: config.yml

        server:
            session:
                enabled: true
                secret_key: cookie_secret
                session_cookie: custom_cookie_name
                max_age: null
                same_site: lax
                https_only: True
                domain: localhost

    For production environment:

    .. code-block:: yaml
        :caption: config.yml

        server:
            session:
                enabled: true
                secret_key: cookie_secret
                session_cookie: custom_cookie_name
                max_age: 3600
                same_site: strict
                https_only: True
                domain: example.com

    """

    enabled: bool = Field(
        default=True,
        description="Set to ``True`` to enable SessionMiddleware",
    )
    secret_key: SecretStr | None = Field(
        default=None,
        description=textwrap.dedent(
            """
            Secret key for encrypting cookies.

            Can be any string. It is recommended to generate random value for every application instance, e.g.:

            .. code:: shell

                pwgen 32 1
            """,
        ),
    )
    session_cookie: str | None = Field(
        default="session",
        description="Name of the session cookie. Change this if there are multiple application under the same domain.",
    )
    max_age: int | None = Field(
        default=14 * 24 * 60 * 60,
        description="Session expiry time in seconds. Defaults to 2 weeks.",
    )
    same_site: str | None = Field(
        default="lax",
        description="Prevents cookie from being sent with cross-site requests.",
    )
    path: str | None = Field(default="/", description="Path to restrict session cookie access.")
    https_only: bool = Field(default=False, description="Secure flag for HTTPS-only access.")
    domain: str | None = Field(
        default=None,
        description="Domain for sharing cookies between subdomains or cross-domains.",
    )

    model_config = ConfigDict(extra="allow")

    @field_validator("secret_key")
    def _validate_secret_key(cls, value: SecretStr | None, info: ValidationInfo) -> SecretStr | None:
        if not value and info.data.get("enabled"):
            raise ValueError("secret_key is required")
        return value
