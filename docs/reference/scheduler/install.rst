.. _server-install:

Install & run scheduler
=======================

With docker
-----------

Installation process
~~~~~~~~~~~~~~~~~~~~

* Install `Docker <https://docs.docker.com/engine/install/>`_
* Install `docker-compose <https://github.com/docker/compose/releases/>`_

* Run the following command:

  .. code:: console

    $ docker compose --profile scheduler up -d --wait

  ``docker-compose`` will download all necessary images, create containers, and then start the server.

  Options can be set via ``.env`` file or ``environment`` section in ``docker-compose.yml``

.. dropdown:: ``docker-compose.yml``

    .. literalinclude:: ../../../docker-compose.yml
        :emphasize-lines: 103-120

.. dropdown:: ``.env.docker``

    .. literalinclude:: ../../../.env.docker
        :emphasize-lines: 4-16,38-39


Without docker
--------------

* Install Python 3.11 or above
* Setup :ref:`database`, run migrations and create partitions
* Create virtual environment

  .. code-block:: console

      $ python -m venv /some/.venv
      $ source /some/.venv/activate

* Install ``syncmaster`` package with following *extra* dependencies:

  .. code-block:: console

      $ pip install syncmaster[scheduler,postgres]

* Run scheduler process

  .. code-block:: console

    $ python -m syncmaster.scheduler
