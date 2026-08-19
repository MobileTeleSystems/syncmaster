# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import textwrap
from typing import Annotated
from urllib.parse import urlparse

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, PostgresDsn, UrlConstraints
from sqlalchemy import make_url


def validate_url(value: PostgresDsn):
    url = make_url(str(value))
    if not url.database:
        msg = "Database URL must contain database name"
        raise ValueError(msg)

    if not url.username or not url.password:
        msg = "Database URL must contain username and password"
        raise ValueError(msg)

    return value


PostgresURL = Annotated[
    PostgresDsn,
    UrlConstraints(allowed_schemes=["postgresql+asyncpg"], default_port=5432, host_required=True),
    AfterValidator(validate_url),
]


class DatabaseSettings(BaseModel):
    """Database connection settings.

    !!! note

        You can pass here any extra option supported by
        [SQLAlchemy Engine class](https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.create_engine),
        even if it is not mentioned in documentation.

    Examples
    --------

    ```yaml title="config.yml"
    database:
        url: postgresql+asyncpg://postgres:postgres@localhost:5432/syncmaster

        # custom option passed directly to SQLAlchemy Engine
        pool_pre_ping: True
    ```
    """

    url: PostgresDsn = Field(
        description=textwrap.dedent(
            """
            Database connection URL.

            Mandatory components:

            * host
            * username (urlencoded)
            * password (urlencoded)

            See [SQLAlchemy documentation](https://docs.sqlalchemy.org/en/20/core/engines.html#server-specific-urls)

            !!! warning

                Only async drivers are supported, e.g. `asyncpg`
            """,
        ),
    )

    @property
    def sync_url(self) -> str:
        schema = urlparse(str(self.url)).scheme
        return str(self.url).replace(schema, "postgresql+psycopg2")

    model_config = ConfigDict(extra="allow")

    def __repr_args__(self):
        safe_url = make_url(str(self.url)).render_as_string(
            hide_password=True,
        )
        extra = super().__repr_args__()
        return [
            ("url", safe_url),
            *[item for item in extra if item[0] != "url"],
        ]
