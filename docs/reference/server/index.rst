.. _server:

REST API Server
===============

SyncMaster server provides simple REST API for accessing entities stored in :ref:`database`.
Implemented using `FastAPI <https://fastapi.tiangolo.com/>`_.

Install & run
-------------

With docker
^^^^^^^^^^^

* Install `Docker <https://docs.docker.com/engine/install/>`_
* Install `docker-compose <https://github.com/docker/compose/releases/>`_

* Run the following command:

  .. code:: console

    $ docker compose --profile server up -d --wait

  ``docker-compose`` will download all necessary images, create containers, and then start the server.

  .. dropdown:: ``docker-compose.yml``

    .. literalinclude:: ../../../docker-compose.yml
        :emphasize-lines: 48-75

  Options can be set via ``config.yml`` file:

  .. dropdown:: ``config.yml``

    .. literalinclude:: ../../../config.yml
        :emphasize-lines: 1-31, 40-49, 70-71

* After server is started and ready, open http://localhost:8000/docs.

Without docker
^^^^^^^^^^^^^^

* Install Python 3.11 or above
* Setup :ref:`database`, run migrations
* Setup :ref:`message-broker`
* Create virtual environment

  .. code-block:: console

      $ python -m venv /some/.venv
      $ source /some/.venv/activate

* Install ``syncmaster`` package with following *extra* dependencies:

  .. code-block:: console

      $ pip install syncmaster[server]

* Run server process

  .. code-block:: console

      $ python -m syncmaster.server --host 0.0.0.0 --port 8000

  This is a thin wrapper around `uvicorn <https://www.uvicorn.org/#command-line-options>`_ cli,
  options and commands are just the same.

* After server is started and ready, open http://localhost:8000/docs.

See also
--------

.. toctree::
    :maxdepth: 1

    auth/index
    configuration/index
    manage_superusers_cli
    openapi
