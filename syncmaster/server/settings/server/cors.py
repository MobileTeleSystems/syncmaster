# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, ConfigDict, Field


class CORSSettings(BaseModel):
    """CORS Middleware Settings.

    See `CORSMiddleware <https://www.starlette.io/middleware/#corsmiddleware>`_ documentation.

    .. note::

        You can pass here any extra option supported by ``CORSMiddleware``,
        even if it is not mentioned in documentation.

    Examples
    --------

    For development environment:

    .. code-block:: yaml
        :caption: config.yml

        server:
            cors:
                enabled: True
                allow_origins: ["*"]
                allow_methods: ["*"]
                allow_headers: ["*"]
                expose_headers: [X-Request-ID, Location, Access-Control-Allow-Credentials]

    For production environment:

    .. code-block:: yaml
        :caption: config.yml

        server:
            cors:
                enabled: True
                allow_origins: [production.example.com]
                allow_methods: [GET]
                allow_headers: [X-Request-ID, X-Request-With]
                expose_headers: [X-Request-ID]
                # custom option passed directly to middleware
                max_age: 600
    """

    enabled: bool = Field(default=True, description="Set to ``True`` to enable middleware")
    allow_origins: list[str] = Field(default_factory=list, description="Domains allowed for CORS")
    allow_credentials: bool = Field(
        default=False,
        description="If ``True``, cookies should be supported for cross-origin request",
    )
    allow_methods: list[str] = Field(default=["GET"], description="HTTP Methods allowed for CORS")
    # https://github.com/snok/asgi-correlation-id#cors
    allow_headers: list[str] = Field(
        default=["X-Request-ID", "X-Request-With"],
        description="HTTP headers allowed for CORS",
    )
    expose_headers: list[str] = Field(default=["X-Request-ID"], description="HTTP headers exposed from server")

    model_config = ConfigDict(extra="allow")
