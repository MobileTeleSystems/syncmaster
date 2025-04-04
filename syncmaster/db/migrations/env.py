# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import asyncio
import os
from logging.config import fileConfig

from alembic import context
from alembic.script import ScriptDirectory
from celery.backends.database.session import ResultModelBase
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from syncmaster.db.models import Base
from syncmaster.server.settings import ServerAppSettings as Settings

config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)

if not config.get_main_option("sqlalchemy.url"):
    # read application settings only if sqlalchemy.url is not being passed via cli arguments
    # TODO: remove settings object creating during import
    config.set_main_option("sqlalchemy.url", Settings().database.url)

target_metadata = (
    Base.metadata,
    ResultModelBase.metadata,
)


def get_next_revision_id():
    script_directory = ScriptDirectory.from_config(context.config)
    versions_path = script_directory.versions

    existing_filenames = os.listdir(versions_path)
    existing_ids = []

    for filename in existing_filenames:
        # Assuming filename format: YYYY-MM-DD_XXXX_slug.py
        parts = filename.split("_")
        if len(parts) >= 2:
            id_part = parts[1]
            try:
                id_num = int(id_part)
                existing_ids.append(id_num)
            except ValueError:
                pass

    if existing_ids:
        next_id = max(existing_ids) + 1
    else:
        next_id = 1

    return next_id


def process_revision_directives(context, revision, directives):
    if directives:
        script = directives[0]
        next_id = get_next_revision_id()
        script.rev_id = f"{next_id:04d}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        process_revision_directives=process_revision_directives,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
