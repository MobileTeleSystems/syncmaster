.. _worker:

Worker
======

SyncMaster worker is a dedicated process which receives new transfer Runs from :ref:`message-broker`,
executes them and updates status & log url in :ref:`database`. Implemented using `Celery <https://docs.celeryq.dev>`_.

.. note::

    Each worker process is bound to one ot more Queues. You have to created it before starting a worker.
    This can be done via :ref:`frontend` or via :ref:`server` REST API.

    Queue field ``slug`` value is then should be passed to Celery argument ``-Q``.
    For example, for slug ``123-test_queue`` this should be ``-Q 123-test_queue``.

Install & run
-------------

With docker
^^^^^^^^^^^

* Install `Docker <https://docs.docker.com/engine/install/>`_
* Install `docker-compose <https://github.com/docker/compose/releases/>`_
* Start :ref:`server` and :ref:`frontend`, create Group and Queue, get slug (e.g. ``test_queue``)
* Run the following command:

  .. code:: console

    $ docker compose --profile worker up -d --wait

  ``docker-compose`` will download all necessary images, create containers, and then start the worker.

  Options can be set via ``.env`` file or ``environment`` section in ``docker-compose.yml``

  .. dropdown:: ``docker-compose.yml``

    .. literalinclude:: ../../../docker-compose.yml
        :emphasize-lines: 84-102

  .. dropdown:: ``.env.docker``

    .. literalinclude:: ../../../.env.docker
        :emphasize-lines: 8-16,40-47

Without docker
^^^^^^^^^^^^^^

* Install Python 3.11 or above
* Install Java 8 or above

  .. code-block:: console

    $ yum install java-1.8.0-openjdk-devel  # CentOS 7
    $ dnf install java-11-openjdk-devel  # CentOS 8
    $ apt-get install openjdk-11-jdk  # Debian-based

* Setup :ref:`database`, run migrations
* Setup :ref:`message-broker`
* Create virtual environment

  .. code-block:: console

      $ python -m venv /some/.venv
      $ source /some/.venv/activate

* Install ``syncmaster`` package with following *extra* dependencies:

  .. code-block:: console

      $ pip install syncmaster[server,worker]

* Start :ref:`server` and :ref:`frontend`
* Create new Group
* Create Queue in this group, and then get **Queue.slug** (e.g. ``123-test_queue``)
* Run worker process:

  .. code-block:: console

    $ python -m celery -A syncmaster.worker.celery worker -Q 123-test_queue --max-tasks-per-child=1

  You can specify options like concurrency and queues by adding additional flags:

  .. code-block:: bash

    $ python -m celery -A syncmaster.worker.celery worker -Q 123-test_queue --max-tasks-per-child=1 --concurrency=4 --loglevel=info

  Refer to the `Celery <https://docs.celeryq.dev/en/stable/>`_ documentation for more advanced start options.

  .. note::

    ``--max-tasks-per-child=1`` flag is important!

See also
--------

.. toctree::
    :maxdepth: 1

    configuration/index
    create_spark_session
    log_url
