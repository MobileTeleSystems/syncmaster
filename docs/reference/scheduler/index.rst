.. _scheduler:

Scheduler
=========

SyncMaster scheduler is a dedicated process which periodically checks scheduler Transfers in :ref:`database`,
and creates corresponding Runs in :ref:`message-broker`.

Implemented using `APScheduler <https://github.com/agronholm/apscheduler>`_.

Install & run
-------------

With docker
^^^^^^^^^^^

* Install `Docker <https://docs.docker.com/engine/install/>`_
* Install `docker-compose <https://github.com/docker/compose/releases/>`_
* Run the following command:

  .. code:: console

    $ docker compose --profile scheduler up -d --wait

  ``docker-compose`` will download all necessary images, create containers, and then start the scheduler.

  .. dropdown:: ``docker-compose.yml``

    .. literalinclude:: ../../../docker-compose.yml
        :emphasize-lines: 98-116

  Options can be set via ``config.yml`` file:

  .. dropdown:: ``config.yml``

    .. literalinclude:: ../../../config.yml
        :emphasize-lines: 1-10,57-58

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

      $ pip install syncmaster[scheduler]

* Run scheduler process:

  .. code-block:: console

    $ python -m syncmaster.Scheduler

  Scheduler currently don't have any command line arguments.

See also
--------

.. toctree::
    :maxdepth: 1

    configuration/index

