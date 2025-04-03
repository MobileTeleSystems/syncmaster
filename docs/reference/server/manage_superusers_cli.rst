.. _manage-superusers-cli:

CLI for managing superusers
===========================

There are two ways to manage users:

* automatic:

  Set ``SYNCMASTER__ENTRYPOINT__SUPERUSERS=user1 user2``, and :ref:`server` Docker container entrypoint
  will automatically set ``is_superuser=True`` flag for them, and reset for other users in database.

* manual via CLI:

.. argparse::
   :module: syncmaster.server.scripts.manage_superusers
   :func: create_parser
   :prog: python -m syncmaster.server.scripts.manage_superusers
