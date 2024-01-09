.. title

==========
SyncMaster
==========


Requirements
============

Python 3.11+

.. documentation

Documentation
=============

.. wiki

Wiki page
=========

.. install

Installation
============

.. Entities

Entities
========

Transfer
--------
A transfer is an object for storing information about the data loading process.
It stores information about the type of connection to the data source, as well as the target table.
The transfer also stores the name of the queue to which the data upload task will be transferred.

Example:

.. code-block:: json

    {
        "group_id": "1",
        "name": "My beautiful transfer.",
        "description": "What a great transfer !",
        "is_scheduled": "False",
        "schedule": "",
        "source_connection_id": "1",
        "target_connection_id": "2",
        "source_params": "{'type': 'postgres', 'table_name': 'source_table'}",
        "target_params": "{'type': 'postgres', 'table_name': 'target_table'}",
        "strategy_params": "{'type': 'full'}",
        "queue_id": "1",
    }

Run
---
This entity represents the launched data upload process. If the transfer is information about unloading
then run is a running process. Run stores information about the startup time as well as its status.
The user cannot create run himself; It is created as a result of executing transfer.

Connection
----------
A connection is an entity for storing information about a database (it doesn’t matter whether it’s a data source or
receiver).

Example:

.. code-block:: json

    {
        "id": "1",
        "name": "Beautiful name",
        "description": "What a great connection !",
        "group_id": "1",
        "connection_data": {
            "type": "postgres",
            "host": "127.0.0.1",
            "port": 5432,
            "database_name": "postgres",
            "additional_params": {},
        },
        "auth_data": {
            "type": "postgres",
            "user": "user_name",
            "passwrod": "password",
        }
    }

Queue
-----
A queue is an entity for specifying on which worker a task will be executed.

Example:

.. code-block:: json

    {
        "id": "1",
        "name": "Beautiful name",
        "description": "What a great queue !",
        "group_id": 1,
    }

.. Roles

Roles and rules
===============

- Users have rights only in the group in which they are registered.
  In a group where they do not exist, they have no rights.
- There can be only one user in a group with the Owner role, all other roles are not limited in
  number.
- Superuser can read, write to the table and delete without being in the group.

All rights indicated in the tables below apply only to resources associated with the user group.

Transfers, Runs and Connections
--------------------------------

.. list-table:: Right to work wirh Transfers, Runs and Connections repositories.
   :header-rows: 1


   * - Rule \ Role
     - Guest
     - User
     - Maintainer
     - Owner
     - Superuser
   * - READ
     - x
     - x
     - x
     - x
     - x
   * - UPDATE, CREATE
     -
     - x
     - x
     - x
     - x
   * - DELETE
     -
     -
     - x
     - x
     - x

Groups
-------

.. list-table:: Rights to work with the groups repository.
   :header-rows: 1

   * - Rule \ Role
     - Guest
     - User
     - Maintainer
     - Owner
     - Superuser
   * - READ
     - x
     - x
     - x
     - x
     - x
   * - UPDATE
     -
     -
     -
     - x
     - x
   * - CREATE, DELETE
     -
     -
     -
     -
     - x

Add user to the group and delete
---------------------------------
Each user has the right to remove himself from a group, regardless of his role in the group.

.. list-table:: Rights to delete and add users to a group.
   :header-rows: 1

   * - Rule \ Role
     - Guest
     - User
     - Maintainer
     - Owner
     - Superuser
   * - READ
     - x
     - x
     - x
     - x
     - x
   * - ADD, UPDATE
     -
     -
     -
     - x
     - x

Queues
------

.. list-table:: Rights to read, delete and update queues.
   :header-rows: 1

   * - Rule \ Role
     - Guest
     - User
     - Maintainer
     - Owner
     - Superuser
   * - READ
     - x
     - x
     - x
     - x
     - x
   * - UPDATE, DELETE, CREATE
     -
     -
     - x
     - x
     - x
