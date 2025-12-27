.. _manage-superusers-cli:

CLI for managing superusers
===========================

There are two ways to manage users:

* automatic

  :ref:`server` Docker container entrypoint will automatically create users with ``is_superuser=True`` in database
  during startup.

  Usernames can be passed via config file:

  .. code-block:: yaml
    :caption: config.yml

    superusers:
        - user1
        - user2

  Or via environment variable:

  .. code-block:: bash

    export 'SYNCMASTER__SUPERUSERS=["user1", "user2"]'

* manual via CLI:

.. argparse::
   :module: syncmaster.server.scripts.manage_superusers
   :func: create_parser
   :prog: python -m syncmaster.server.scripts.manage_superusers
