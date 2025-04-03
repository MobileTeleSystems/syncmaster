.. _database:

Relation Database
=================

SyncMaster requires relational database for storing internal data.

Currently, SyncMaster supports only `PostgreSQL <https://www.postgresql.org/>`_ as storage for lineage entities and relations.

Migrations
------------

After a database is started, it is required to run migration script.
For empty database, it creates all the required tables and indexes.
For non-empty database, it will perform database structure upgrade, using `Alembic <https://alembic.sqlalchemy.org/>`_.

.. warning::

    Other containers (server, scheduler, worker) should be stopped while running migrations, to prevent interference.

Requirements
------------

* PostgreSQL 12 or higher. It is recommended to use latest Postgres version.

Install & run
-------------

With Docker
~~~~~~~~~~~

* Install `Docker <https://docs.docker.com/engine/install/>`_
* Install `docker-compose <https://github.com/docker/compose/releases/>`_

* Run the following command:

  .. code:: console

    $ docker compose up -d db db-migrations

  ``docker-compose`` will download PostgreSQL image, create container and volume, and then start container.
  Image entrypoint will create database if volume is empty.

  After that, one-off container with migrations script will run.

  Options can be set via ``.env`` file or ``environment`` section in ``docker-compose.yml``

  .. dropdown:: ``docker-compose.yml``

      .. literalinclude:: ../../../docker-compose.yml
          :emphasize-lines: 1-31,142

  .. dropdown:: ``.env.docker``

      .. literalinclude:: ../../../.env.docker
          :emphasize-lines: 8-9

Without Docker
~~~~~~~~~~~~~~

* For installing PostgreSQL, please follow `installation instruction <https://www.postgresql.org/download/>`_.
* Install Python 3.11 or above
* Create virtual environment

  .. code-block:: console

      $ python -m venv /some/.venv
      $ source /some/.venv/activate

* Install ``syncmaster`` package with following *extra* dependencies:

  .. code-block:: console

      $ pip install syncmaster[postgres]

* Configure :ref:`Database connection <configuration-database>` using environment variables, e.g. by creating ``.env`` file:

  .. code-block:: console
    :caption: /some/.env

    $ export SYNCMASTER__DATABASE__URL=postgresql+asyncpg://syncmaster:changeme@db:5432/syncmaster

  And then read values from this file:

  .. code:: console

    $ source /some/.env

* Run migrations:

  .. code:: console

    $ python -m syncmaster.db.migrations upgrade head

  This is a thin wrapper around `alembic cli <https://alembic.sqlalchemy.org/en/latest/tutorial.html#running-our-first-migration>`_,
  options and commands are just the same.

  .. note::

      This command should be executed after each upgrade to new Data.Rentgen version.

See also
--------

.. toctree::
    :maxdepth: 1

    configuration
    credentials_encryption
