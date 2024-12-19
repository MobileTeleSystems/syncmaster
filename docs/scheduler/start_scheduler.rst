Starting the Scheduler
======================

With docker
-----------

Installation process
~~~~~~~~~~~~~~~~~~~~

Docker will download worker image of syncmaster scheduler & broker, and run them.
Options can be set via ``.env`` file or ``environment`` section in ``docker-compose.yml``

.. dropdown:: ``docker-compose.yml``

    .. literalinclude:: ../../docker-compose.yml
        :emphasize-lines: 90-103

.. dropdown:: ``.env.docker``

    .. literalinclude:: ../../.env.docker
        :emphasize-lines: 11-25

To start the worker container you need to run the command:

.. code-block:: bash

    docker compose up scheduler -d --wait --wait-timeout 200


Without docker
--------------

To start the scheduler you need to run the command

.. code-block:: bash

    python -m syncmaster.scheduler


