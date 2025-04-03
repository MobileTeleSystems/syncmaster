# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from syncmaster.server.settings.auth import AuthSettings
from syncmaster.server.settings.server import ServerSettings
from syncmaster.settings import (
    CredentialsEncryptionSettings,
    DatabaseSettings,
    LoggingSettings,
    RabbitMQSettings,
)


class ServerAppSettings(BaseSettings):
    """Syncmaster server settings.

    Server can be configured in 2 ways:

    * By explicitly passing ``settings`` object as an argument to :obj:`application_factory <syncmaster.server.main.application_factory>`
    * By setting up environment variables matching a specific key.

    All environment variable names are written in uppercase and should be prefixed with ``SYNCMASTER__``.
    Nested items are delimited with ``__``.

    More details can be found in
    `Pydantic documentation <https://docs.pydantic.dev/latest/concepts/pydantic_settings/>`_.

    Examples
    --------

    .. code-block:: bash

        # same as settings.database.url = "postgresql+asyncpg://postgres:postgres@localhost:5432/syncmaster"
        SYNCMASTER__DATABASE__URL=postgresql+asyncpg://postgres:postgres@localhost:5432/syncmaster

        # same as settings.server.debug = True
        SYNCMASTER__SERVER__DEBUG=True
    """

    database: DatabaseSettings = Field(description=":ref:`Database settings <server-configuration-database>`")
    broker: RabbitMQSettings = Field(description=":ref:`Broker settings <server-configuration-broker>`")
    logging: LoggingSettings = Field(
        default_factory=LoggingSettings,
        description=":ref:`Logging settings <server-configuration-logging>`",
    )
    server: ServerSettings = Field(
        default_factory=ServerSettings,
        description=":ref:`Server settings <server-configuration>`",
    )
    auth: AuthSettings = Field(
        default_factory=AuthSettings,
        description=":ref:`Auth provider settings <server-auth-providers>`",
    )
    encryption: CredentialsEncryptionSettings = Field(
        default_factory=CredentialsEncryptionSettings,  # type: ignore[arg-type]
        description="Settings for encrypting credential data",
    )

    model_config = SettingsConfigDict(env_prefix="SYNCMASTER__", env_nested_delimiter="__")
