# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

import logging
import textwrap
from logging.config import dictConfig
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

LOG_PATH = Path(__file__).parent.resolve()
logger = logging.getLogger(__name__)


class LoggingSetupError(Exception):
    pass


def setup_logging(config_path: Path) -> None:
    """Parse file with logging configuration, and setup logging accordingly"""
    if not config_path.exists():
        raise OSError(f"Logging configuration file '{config_path}' does not exist")

    try:
        config = yaml.safe_load(config_path.read_text())
        dictConfig(config)
    except Exception as e:
        raise LoggingSetupError(f"Error reading logging configuration '{config_path}'") from e


class LoggingSettings(BaseModel):
    """Logging Settings.

    Examples
    --------

    Using ``json`` preset:

    .. code-block:: bash

        SYNCMASTER__LOGGING__SETUP=True
        SYNCMASTER__LOGGING__PRESET=json

    Passing custom logging config file:

    .. code-block:: bash

        SYNCMASTER__LOGGING__SETUP=True
        SYNCMASTER__LOGGING__CUSTOM__CONFIG_PATH=/some/logging.yml

    Setup logging in some other way, e.g. using `uvicorn args <https://www.uvicorn.org/settings/#logging>`_:

    .. code-block:: bash

        $ export SYNCMASTER__LOGGING__SETUP=False
        $ python -m syncmaster.server --log-level debug
    """

    setup: bool = Field(
        default=True,
        description="If ``True``, setup logging during application start",
    )
    preset: Literal["json", "plain", "colored"] = Field(
        default="plain",
        description=textwrap.dedent(
            """
            Name of logging preset to use.

            There are few logging presets bundled to ``syncmaster[server]`` package:

            .. dropdown:: ``plain`` preset

                This preset is recommended to use in environment which do not support colored output,
                e.g. CI jobs

                .. literalinclude:: ../../../../syncmaster/settings/log/plain.yml

            .. dropdown:: ``colored`` preset

                This preset is recommended to use in development environment,
                as it simplifies debugging. Each log record is output with color specific for a log level

                .. literalinclude:: ../../../../syncmaster/settings/log/colored.yml

            .. dropdown:: ``json`` preset

                This preset is recommended to use in production environment,
                as it allows to avoid writing complex log parsing configs. Each log record is output as JSON line

                .. literalinclude:: ../../../../syncmaster/settings/log/json.yml
            """,
        ),
    )

    custom_config_path: Path | None = Field(
        default=None,
        description=textwrap.dedent(
            """
            Path to custom logging configuration file. If set, overrides :obj:`~preset` value.

            File content should be in YAML format and conform
            `logging.dictConfig <https://docs.python.org/3/library/logging.config.html#logging-config-dictschema>`_.
            """,
        ),
    )

    def get_log_config_path(self) -> Path:
        return self.custom_config_path or LOG_PATH / f"{self.preset}.yml"
