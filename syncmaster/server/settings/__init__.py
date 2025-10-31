# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import Field

from syncmaster.server.settings.auth import AuthSettings
from syncmaster.server.settings.server import ServerSettings
from syncmaster.settings import (
    DEFAULT_LOGGING_SETTINGS,
    BaseSettings,
    CredentialsEncryptionSettings,
    DatabaseSettings,
    LoggingSettings,
    RabbitMQSettings,
)


class ServerAppSettings(BaseSettings):
    """Server application settings.

    The settings can be passed in several ways:

    1. By storing settings in a configuration file ``config.yml`` (preferred).
    2. By setting environment variables matching specific keys (``SYNCMASTER__DATABASE__URL`` == ``database.url``).
    3. By explicitly passing a settings object as an argument of application factory function.

    More details can be found in
    `Pydantic documentation <https://docs.pydantic.dev/latest/concepts/pydantic_settings/>`_.

    Examples
    --------

    .. code-block:: yaml
        :caption: config.yml

        database:
            url: postgresql+asyncpg://postgres:postgres@localhost:5432/syncmaster

        broker:
            url: amqp://user:password@localhost:5672/

        logging: {}
        encryption: {}
        server: {}
        auth: {}
    """

    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings,  # type: ignore[arg-type]
        description=":ref:`Database settings <server-configuration-database>`",
    )
    broker: RabbitMQSettings = Field(
        default_factory=RabbitMQSettings,  # type: ignore[arg-type]
        description=":ref:`Broker settings <server-configuration-broker>`",
    )
    logging: LoggingSettings = Field(
        default=DEFAULT_LOGGING_SETTINGS,
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
