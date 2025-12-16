.. _frontend:

Frontend
========

SyncMaster provides a `Frontend (UI) <https://github.com/MobileTeleSystems/syncmaster-ui>`_ based on `React <https://react.dev/>`_,
providing users the ability to create, update, delete entitities.

Install & run
-------------

With Docker
~~~~~~~~~~~

* Install `Docker <https://docs.docker.com/engine/install/>`_
* Install `docker-compose <https://github.com/docker/compose/releases/>`_

* Run the following command:

  .. code:: console

    $ docker compose --profile frontend up -d --wait

  ``docker-compose`` will download SyncMaster UI image, create containers, and then start them.

  .. dropdown:: ``docker-compose.yml``

      .. literalinclude:: ../../../docker-compose.yml
          :emphasize-lines: 118-130

  Options can be set via ``config.yml`` file:

  .. dropdown:: ``config.yml``

      .. literalinclude:: ../../../config.yml
          :emphasize-lines: 34-37

* After frontend is started and ready, open http://localhost:3000.

See also
--------

.. toctree::
    :maxdepth: 1

    configuration
