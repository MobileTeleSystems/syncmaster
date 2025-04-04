# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import textwrap
from urllib.parse import urlparse, urlunparse

from pydantic import BaseModel, ConfigDict, Field


class DatabaseSettings(BaseModel):
    """Database connection settings.

    .. note::

        You can pass here any extra option supported by
        `SQLAlchemy Engine class <https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.create_engine>`_,
        even if it is not mentioned in documentation.

    Examples
    --------

    .. code-block:: bash

        DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/syncmaster
        # custom option passed directly to engine factory
        DATABASE_POOL_PRE_PING=True
    """

    url: str = Field(
        description=textwrap.dedent(
            """
            Database connection URL.

            See `SQLAlchemy documentation <https://docs.sqlalchemy.org/en/20/core/engines.html#server-specific-urls>`_

            .. warning:

                Only async drivers are supported, e.g. ``asyncpg``
            """,
        ),
    )

    @property
    def sync_url(self) -> str:
        parsed_url = urlparse(self.url)
        # replace '+asyncpg' with '+psycopg2' in the scheme - used by celery
        scheme = parsed_url.scheme.replace("+asyncpg", "+psycopg2")
        sync_parsed_url = parsed_url._replace(scheme=scheme)
        return urlunparse(sync_parsed_url)

    model_config = ConfigDict(extra="allow")
