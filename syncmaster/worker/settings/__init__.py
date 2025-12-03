# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Any

from pydantic import BaseModel, Field
from pydantic.types import ImportString

from syncmaster.settings import (
    DEFAULT_LOGGING_SETTINGS,
    BaseSettings,
    CredentialsEncryptionSettings,
    DatabaseSettings,
    LoggingSettings,
    RabbitMQSettings,
)
from syncmaster.worker.settings.hwm_store import HWMStoreSettings


class WorkerSettings(BaseModel):
    """Celery worker settings.

    Examples
    --------

    .. code-block:: yaml
        :caption: config.yml

        worker:
            log_url_template: "https://logs.location.example.com/syncmaster-worker?correlation_id={{ correlation_id }}&run_id={{ run.id }}"

            create_spark_session_function: custom_syncmaster.spark.get_worker_spark_session
            spark_session_default_config:
                spark.master: local
                spark.driver.host: 127.0.0.1
                spark.driver.bindAddress: 0.0.0.0
                spark.sql.pyspark.jvmStacktrace.enabled: true
                spark.ui.enabled: false
    """

    create_spark_session_function: ImportString = Field(
        "syncmaster.worker.spark.get_worker_spark_session",
        description="Function to create Spark session for worker",
        validate_default=True,
    )
    spark_session_default_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Default Spark session configuration",
    )
    log_url_template: str = Field(
        "",
        description=":ref:`URL template to access worker logs <worker-log-url>`",
    )


class WorkerAppSettings(BaseSettings):
    """
    Worker application settings.

    This class is used to configure various settings for the worker application.
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
        worker: {}
        hwm_store: {}
    """

    database: DatabaseSettings = Field(default_factory=DatabaseSettings, description="Database settings")
    broker: RabbitMQSettings = Field(default_factory=RabbitMQSettings, description="Broker settings")
    logging: LoggingSettings = Field(default=DEFAULT_LOGGING_SETTINGS, description="Logging settings")
    worker: WorkerSettings = Field(description="Worker-specific settings")
    encryption: CredentialsEncryptionSettings = Field(
        default_factory=CredentialsEncryptionSettings,
        description="Settings for encrypting credential data",
    )
    hwm_store: HWMStoreSettings = Field(default_factory=HWMStoreSettings, description="HWM Store settings")
