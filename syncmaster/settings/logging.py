# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import logging
import logging.config  # noqa: WPS301, WPS458

from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from pydantic_settings_logging import (
    FilterConfig,
    FormatterConfig,
    HandlerConfig,
    LoggerConfig,
)
from pydantic_settings_logging import LoggingSettings as BaseLoggingSettings
from pydantic_settings_logging import (
    RootLoggerConfig,
    StreamHandlerConfig,
)


# https://github.com/vduseev/pydantic-settings-logging/pull/1
class CallableFactoryConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    callable: str = Field(
        description="Custom callable",
        validation_alias=AliasChoices("callable", "()"),
        serialization_alias="()",
    )


class LoggingSettings(BaseLoggingSettings):
    """Python logging configuration.

    See `logging.config <https://docs.python.org/3/library/logging.config.html#dictionary-schema-details>`_ docs.

    Logging to ``stdout`` with colored text:

    .. code-block:: yaml
        :caption: config.yml

        logging:
            # development usage only
            version: 1
            disable_existing_loggers: false

            filters:
                # Add request ID as extra field named `correlation_id` to each log record.
                # This is used in combination with settings.server.request_id.enabled=True
                # See https://github.com/snok/asgi-correlation-id#configure-logging
                correlation_id:
                    (): asgi_correlation_id.CorrelationIdFilter
                    uuid_length: 32
                    default_value: '-'

            formatters:
                colored:
                    class: coloredlogs.ColoredFormatter
                    # Add correlation_id to log records
                    format: '%(asctime)s.%(msecs)03d %(processName)s:%(process)d %(name)s:%(lineno)d [%(levelname)s] %(correlation_id)s %(message)s'
                    datefmt: '%Y-%m-%d %H:%M:%S'

            handlers:
                main:
                    class: logging.StreamHandler
                    formatter: colored
                    filters: [correlation_id]
                    stream: ext://sys.stdout

            root:
                handlers: [main]
                level: INFO

            loggers:
                uvicorn:
                    handlers: [main]
                    level: INFO
                    propagate: false
                celery:
                    handlers: [main]
                    level: INFO
                    propagate: false
                scheduler:
                    handlers: [main]
                    level: INFO
                    propagate: false
                py4j:
                    handlers: [main]
                    level: WARNING
                    propagate: false
                hdfs.client:
                    handlers: [main]
                    level: WARNING
                    propagate: false


    Logging to ``stdout`` without colored text:

    .. code-block:: yaml
        :caption: config.yml

        logging:
            # development usage only
            version: 1
            disable_existing_loggers: false

            filters:
                # Add request ID as extra field named `correlation_id` to each log record.
                # This is used in combination with settings.server.request_id.enabled=True
                # See https://github.com/snok/asgi-correlation-id#configure-logging
                correlation_id:
                    class: asgi_correlation_id.CorrelationIdFilter
                    uuid_length: 32
                    default_value: '-'

            formatters:
                plain:
                    (): logging.Formatter
                    # Add correlation_id to log records
                    format: '%(asctime)s.%(msecs)03d %(processName)s:%(process)d %(name)s:%(lineno)d [%(levelname)s] %(correlation_id)s %(message)s'
                    datefmt: '%Y-%m-%d %H:%M:%S'

            handlers:
                main:
                    class: logging.StreamHandler
                    formatter: plain
                    filters: [correlation_id]
                    stream: ext://sys.stdout

            root:
                handlers: [main]
                level: INFO

            loggers:
                uvicorn:
                    handlers: [main]
                    level: INFO
                    propagate: false
                celery:
                    handlers: [main]
                    level: INFO
                    propagate: false
                scheduler:
                    handlers: [main]
                    level: INFO
                    propagate: false
                py4j:
                    handlers: [main]
                    level: WARNING
                    propagate: false
                hdfs.client:
                    handlers: [main]
                    level: WARNING
                    propagate: false


    Logging to ``stdout`` in JSON format:

    .. code-block:: yaml
        :caption: config.yml

        logging:
            version: 1
            disable_existing_loggers: false

            filters:
                # Add request ID as extra field named `correlation_id` to each log record.
                # This is used in combination with settings.server.request_id.enabled=True
                # See https://github.com/snok/asgi-correlation-id#configure-logging
                correlation_id:
                    (): asgi_correlation_id.CorrelationIdFilter
                    uuid_length: 32
                    default_value: '-'

            formatters:
                json:
                    (): pythonjsonlogger.jsonlogger.JsonFormatter
                    # Add correlation_id to log records
                    fmt: '%(processName)s %(process)d %(threadName)s %(thread)d %(name)s %(lineno)d %(levelname)s %(message)s %(correlation_id)s'
                    timestamp: true

            handlers:
                main:
                    class: logging.StreamHandler
                    formatter: json
                    filters: [correlation_id]
                    stream: ext://sys.stdout

            root:
                handlers: [main]
                level: INFO

            loggers:
                uvicorn:
                    handlers: [main]
                    level: INFO
                    propagate: false
                celery:
                    handlers: [main]
                    level: INFO
                    propagate: false
                scheduler:
                    handlers: [main]
                    level: INFO
                    propagate: false
                py4j:
                    handlers: [main]
                    level: WARNING
                    propagate: false
                hdfs.client:
                    handlers: [main]
                    level: WARNING
                    propagate: false

    """  # noqa: E501

    filters: dict[str, FilterConfig | CallableFactoryConfig] = Field(
        default_factory=dict,
        description="Logging filters",
    )
    formatters: dict[str, FormatterConfig | CallableFactoryConfig] = Field(
        default_factory=dict,
        description="Logging formatters",
    )
    handlers: dict[str, HandlerConfig | CallableFactoryConfig] = Field(
        default_factory=dict,
        description="Logging handlers",
    )


DEFAULT_LOGGING_SETTINGS = LoggingSettings(
    disable_existing_loggers=False,
    filters={
        # Add request ID as extra field named `correlation_id` to each log record.
        # This is used in combination with settings.server.request_id.enabled=True
        # See https://github.com/snok/asgi-correlation-id#configure-logging
        "correlation_id": CallableFactoryConfig(
            callable="asgi_correlation_id.CorrelationIdFilter",
            uuid_length=32,
            default_value="-",
        ),
    },
    formatters={
        "colored": FormatterConfig(
            class_="coloredlogs.ColoredFormatter",
            format=(
                "%(asctime)s.%(msecs)03d %(processName)s:%(process)d %(name)s:%(lineno)d [%(levelname)s] %(correlation_id)s %(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
        ),
    },
    handlers={
        "main": StreamHandlerConfig(
            formatter="colored",
            filters=["correlation_id"],
            stream="ext://sys.stdout",
        ),
    },
    root=RootLoggerConfig(
        handlers=["main"],
        level="INFO",
    ),
    loggers={
        "uvicorn": LoggerConfig(
            handlers=["main"],
            level="INFO",
            propagate=False,
        ),
        "celery": LoggerConfig(
            handlers=["main"],
            level="INFO",
            propagate=False,
        ),
        "py4j": LoggerConfig(
            handlers=["main"],
            level="WARNING",
            propagate=False,
        ),
        "hdfs.client": LoggerConfig(
            handlers=["main"],
            level="WARNING",
            propagate=False,
        ),
    },
)


def setup_logging(settings: LoggingSettings):
    logging.config.dictConfig(settings.model_dump())
