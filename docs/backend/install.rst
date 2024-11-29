.. _backend-install:

Install & run backend
=====================

With docker
-----------

Requirements
~~~~~~~~~~~~

* `Docker <https://docs.docker.com/engine/install/>`_
* `docker-compose <https://github.com/docker/compose/releases/>`_

Installation process
~~~~~~~~~~~~~~~~~~~~

Docker will download backend image of syncmaster & Postgres, and run them.
Options can be set via ``.env`` file or ``environment`` section in ``docker-compose.yml``

.. dropdown:: ``docker-compose.yml``

    .. literalinclude:: ../../docker-compose.yml

.. dropdown:: ``.env.docker``

    .. literalinclude:: ../../.env.docker

After container is started and ready, open http://localhost:8000/docs.

Managing superusers
^^^^^^^^^^^^^^^^^^^

Users listed in ``SYNCMASTER__ENTRYPOINT__SUPERUSERS`` env variable will be automatically promoted to ``SUPERUSER`` role.

Adding superusers:

.. code-block:: console

    $ python -m syncmaster.backend.scripts.manage_superusers add <username1> <username2>

Removing superusers:

.. code-block:: console

    $ python -m syncmaster.backend.scripts.manage_superusers remove <username1> <username2>

Viewing list of superusers:

.. code-block:: console

    $ python -m syncmaster.backend.scripts.manage_superusers list

Without docker
--------------

Requirements
~~~~~~~~~~~~

* Python 3.7 or above
* Pydantic 2.x
* Some relation database instance, like `Postgres <https://www.postgresql.org/>`_

Installation process
~~~~~~~~~~~~~~~~~~~~

Install ``data-syncmaster`` package with following *extra* dependencies:

.. code-block:: console

    $ pip install data-syncmaster[backend,worker]

Available *extras* are:

* ``backend`` - main backend requirements, like FastAPI, SQLAlchemy and so on.
* ``worker`` - this dependency is needed to install the worker.


Run database
~~~~~~~~~~~~

Start Postgres instance somewhere, and set up environment variable:

.. code-block:: bash

    SYNCMASTER__DATABASE__URL=postgresql+asyncpg://syncmaster:changeme@db:5432/syncmaster

You can use virtually any database supported by `SQLAlchemy <https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls>`_,
but the only one we really tested is Postgres.

Run migrations
~~~~~~~~~~~~~~

To apply migrations (database structure changes) you need to execute following command:

.. code-block:: console

    $ python -m syncmaster.db.migrations upgrade head

This is a thin wrapper around `alembic <https://alembic.sqlalchemy.org/en/latest/tutorial.html#running-our-first-migration>`_ cli,
options and commands are just the same.

.. note::

    This command should be executed after each upgrade to new SyncMaster version.

Run RabbitMQ
~~~~~~~~~~~~

Start RabbitMQ instance somewhere, and set up environment variable:

.. code-block:: bash

    SYNCMASTER__BROKER__URL=amqp://guest:guest@rabbitmq:5672/

Run backend
~~~~~~~~~~~

To start backend server you need to execute following command:

.. code-block:: console

    $ python -m syncmaster.backend --host 0.0.0.0 --port 8000

After server is started and ready, open http://localhost:8000/docs.
