.. _message-broker:

Message Broker
==============

Message broker is componen used by :ref:`server`/:ref:`scheduler` to communicate with :ref:`worker`.

SyncMaster can work virtually with any broker supported by `Celery <https://docs.celeryq.dev>`_.
But the only broker we tested is `RabbitMQ <https://www.rabbitmq.com/>`_.

Requirements
------------

* RabbitMQ 4.x. It is recommended to use latest RabbitMQ version.

Setup
~~~~~

With Docker
^^^^^^^^^^^

* Install `Docker <https://docs.docker.com/engine/install/>`_
* Install `docker-compose <https://github.com/docker/compose/releases/>`_
* Run the following command:

  .. code:: console

    $ docker compose --profile broker up -d --wait

  ``docker-compose`` will download RabbitMQ image, create container and volume, and then start container.
  Image entrypoint will create database if volume is empty.

  .. dropdown:: ``docker-compose.yml``

    .. literalinclude:: ../../../docker-compose.yml
        :emphasize-lines: 34-46,134

  Options can be set via ``config.yml`` file:

  .. dropdown:: ``config.yml``

    .. literalinclude:: ../../../config.yml
        :emphasize-lines: 4-5

Without Docker
^^^^^^^^^^^^^^

Please follow `RabbitMQ installation instruction <https://www.rabbitmq.com/docs/download>`_.
