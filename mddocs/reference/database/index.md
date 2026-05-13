# Relation Database { #database }

SyncMaster requires relational database for storing internal data.

Currently, SyncMaster supports only [PostgreSQL](https://www.postgresql.org/).

## Migrations

After a database is started, it is required to run migration script.
For empty database, it creates all the required tables and indexes.
For non-empty database, it will perform database structure upgrade, using [Alembic](https://alembic.sqlalchemy.org/).

!!! warning
    Other containers (server, scheduler, worker) should be stopped while running migrations, to prevent interference.

## Requirements

- PostgreSQL 12 or higher. It is recommended to use latest Postgres version.

## Install & run

### With Docker

- Install [Docker](https://docs.docker.com/engine/install/)

- Install [docker-compose](https://github.com/docker/compose/releases/)

- Run the following command:

  ```console
  $ docker compose up -d db db-migrations
  ...
  ```

  `docker-compose` will download PostgreSQL image, create container and volume, and then start container.
  Image entrypoint will create database if volume is empty.

  After that, one-off container with migrations script will run.

  Options can be set via `config.yml` file.

### `docker-compose.yml`

--8<--
docker-compose.yml:1:32,133
--8<--

### `config.yml`

--8<--
config.yml:1:2
--8<--

### Without Docker

- For installing PostgreSQL, please follow [installation instruction](https://www.postgresql.org/download/).

- Install Python 3.11 or above

- Create virtual environment

  ```console
  $ python -m venv /some/.venv
  $ source /some/.venv/activate
  ...
  ```

- Install `syncmaster` package with following *extra* dependencies:

  ```console
  $ pip install data-syncmaster[postgres]
  ...
  ```

- Configure [Database connection][configuration-database] using environment variables, e.g. by creating `.env` file:

  ```console
  $ export SYNCMASTER__DATABASE__URL=postgresql+asyncpg://syncmaster:changeme@db:5432/syncmaster
  ...
  ```

  And then read values from this file:

  ```console
  $ source /some/.env
  ...
  ```

- Run migrations:

  ```console
  $ python -m syncmaster.db.migrations upgrade head
  ...
  ```

  This is a thin wrapper around [alembic cli](https://alembic.sqlalchemy.org/en/latest/tutorial.html#running-our-first-migration),
  options and commands are just the same.

> **This command should be executed after each upgrade to new Data.SyncMaster version.**

## See also

- [Database settings][configuration-database]
- [Credentials encryption][configuration-credentials-encryption]
- [Database structure][database-structure]
