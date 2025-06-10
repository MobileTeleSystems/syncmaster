# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0


import textwrap

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class SessionSettings(BaseModel):
    """Session Middleware Settings.

    See `SessionMiddleware <https://www.starlette.io/middleware/#sessionmiddleware>`_ documentation.

    .. note::

        You can pass here any extra option supported by ``SessionMiddleware``,
        even if it is not mentioned in documentation.

    Examples
    --------

    For development environment:

    .. code-block:: bash

        SYNCMASTER__SERVER__SESSION__SECRET_KEY=secret
        SYNCMASTER__SERVER__SESSION__SESSION_COOKIE=custom_cookie_name
        SYNCMASTER__SERVER__SESSION__MAX_AGE=None  # cookie will last as long as the browser session
        SYNCMASTER__SERVER__SESSION__SAME_SITE=strict
        SYNCMASTER__SERVER__SESSION__HTTPS_ONLY=True
        SYNCMASTER__SERVER__SESSION__DOMAIN=example.com

    For production environment:

    .. code-block:: bash

        SYNCMASTER__SERVER__SESSION__SECRET_KEY=secret
        SYNCMASTER__SERVER__SESSION__HTTPS_ONLY=True

    """

    secret_key: SecretStr = Field(
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
