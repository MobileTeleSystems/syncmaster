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

Start Postgres instance somewhere, and set up environment variables:

.. code-block:: bash

    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432
    POSTGRES_DB=postgres
    POSTGRES_USER=user
    POSTGRES_PASSWORD=password

You can use virtually any database supported by `SQLAlchemy <https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls>`_,
but the only one we really tested is Postgres.

Set environment variables to connect to RabbitMQ
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set variables to connect to RabbitMQ

.. code-block:: bash
    RABBITMQ_HOST=somehost
    RABBITMQ_PORT=5672
    RABBITMQ_USER=user
    RABBITMQ_PASSWORD=password

Run worker
~~~~~~~~~~

.. note::

    Before starting the worker you need to create a queue.
    The queue is created by sending a post request to ``/queues`` endpoint (See Swagger doc for details).

to start the worker you need to run the command

.. code-block:: console

    $ celery -A syncmaster.worker.config.celery worker --loglevel=info --max-tasks-per-child=1 -Q queue_name

.. note::

    The specified celery options are given as an example, you can specify other options you need.


Run backend
~~~~~~~~~~~

To start backend server you need to execute following command:

.. code-block:: console

    $ python -m syncmaster.backend.main

After server is started and ready, open http://localhost:8000/docs.
