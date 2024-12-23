.. _worker-install:

Install & run worker
====================

.. note::

    Before starting the worker you need to create a queue.
    The queue is created by sending a post request to ``/queues`` endpoint (See Swagger doc for details).

With docker
-----------

Installation process
~~~~~~~~~~~~~~~~~~~~

Docker will download worker image, and then start worker container with dependencies.
Options can be set via ``.env`` file or ``environment`` section in ``docker-compose.yml``

.. dropdown:: ``docker-compose.yml``

    .. literalinclude:: ../../docker-compose.yml
        :emphasize-lines: 77-91

.. dropdown:: ``.env.docker``

    .. literalinclude:: ../../.env.docker
        :emphasize-lines: 4-16

To start the worker container you need to run the command:

.. code-block:: bash

    docker compose up worker -d --wait --wait-timeout 200


Without docker
--------------

To start the worker you need to run the command

.. code-block:: bash

    python -m celery -A syncmaster.worker.celery worker --max-tasks-per-child=1

You can specify options like concurrency and queues by adding additional flags:

.. code-block:: bash

    python -m celery -A syncmaster.worker.celery worker --concurrency=4 --max-tasks-per-child=1 --loglevel=info


Refer to the `Celery <https://docs.celeryq.dev/en/stable/>`_ documentation for more advanced start options.
