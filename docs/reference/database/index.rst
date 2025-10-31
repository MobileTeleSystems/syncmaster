.. _database:

Relation Database
=================

SyncMaster requires relational database for storing internal data.

Currently, SyncMaster supports only `PostgreSQL <https://www.postgresql.org/>`_.

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

  .. dropdown:: ``docker-compose.yml``

      .. literalinclude:: ../../../docker-compose.yml
          :emphasize-lines: 1-32,133

  Options can be set via ``config.yml`` file:

  .. dropdown:: ``config.yml``

      .. literalinclude:: ../../../config.yml
          :emphasize-lines: 1-2

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

* Configure :ref:`Database connection <configuration-database>` by creating config file:

  .. code-block:: yaml
    :caption: /some/config.yml

    database:
        url: postgresql+asyncpg://syncmaster:changeme@db:5432/syncmaster

  File should be created in current directory. If not, you can override its location via environment variable:

  .. code:: console

    $ export SYNCMASTER_CONFIG_FILE=/some/config.yml

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
    structure
