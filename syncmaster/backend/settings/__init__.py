# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from enum import StrEnum

from pydantic import Field
from pydantic.types import ImportString

from syncmaster.backend.settings.auth import AuthSettings
from syncmaster.backend.settings.server import ServerSettings
from syncmaster.settings import SyncmasterSettings


class EnvTypes(StrEnum):
    LOCAL = "LOCAL"


class BackendSettings(SyncmasterSettings):
    """Syncmaster backend settings.

    Backend can be configured in 2 ways:

    * By explicitly passing ``settings`` object as an argument to :obj:`application_factory <syncmaster.backend.main.application_factory>`
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

    server: ServerSettings = Field(
        default_factory=ServerSettings,
        description="Server settings <backend-configuration",
    )
    auth: AuthSettings = Field(
        default_factory=AuthSettings,
        description="Auth settings",
    )

    class Config:
        env_prefix = "SYNCMASTER__"
        env_nested_delimiter = "__"
