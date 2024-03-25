.. title

==========
SyncMaster
==========

|Coverage|

.. |Coverage| image:: https://codecov.io/gh/MobileTeleSystems/syncmaster/graph/badge.svg?token=ky7UyUxolB
 :target: https://codecov.io/gh/MobileTeleSystems/syncmaster


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

User
----

This is representation of user which can access the application.
It is automatically created during first login, no special registration step is needed.

User can be marked as superuser. Such user has priviliges to do anything they want.
Usually there are a few superusers within the entire application.

Example:

.. code-block:: json

    {
        "username": "msmarty5",
        "is_superuser": False,
        "is_active": True,
    }

Group
-----

Other objects (like connection, transfer, run, queue) can be created only within some group (see ``group_id``).

Note: currently groups can be created only by superuser.

Example:

.. code-block:: json

    {
        "name": "Some group",
        "description": "",
        "owner_id": 123,
    }

Connection
----------
A connection is an entity for storing information about a database (it doesn’t matter whether it’s a data source or
receiver).

Example:

.. code-block:: json

    {
        "group_id": "1",
        "name": "Beautiful name",
        "description": "What a great connection !",
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
            "password": "password",
        }
    }

Queue
-----
A queue is an entity for specifying on which set of workers a task will be executed. This is just a as Celery queue.

Example:

.. code-block:: json

    {
        "group_id": 1,
        "name": "Beautiful name",
        "description": "What a great queue !",
    }

Runs are send to a specific queue. Celery workers can be assigned to one or multiple queues to handle those runs.

Transfer
--------
A transfer is an object for storing information about the data loading process.
It stores information like source connection, target connection, table name and so on.
The transfer also stores the name of the queue to which the data upload task will be transferred.

Example:

.. code-block:: json

    {
        "group_id": "1",
        "queue_id": "1",
        "name": "My beautiful transfer.",
        "description": "What a great transfer !",
        "is_scheduled": "False",
        "schedule": "",
        "source_connection_id": "1",
        "target_connection_id": "2",
        "source_params": "{'type': 'postgres', 'table_name': 'source_table'}",
        "target_params": "{'type': 'postgres', 'table_name': 'target_table'}",
        "strategy_params": "{'type': 'full'}",
    }

Run
---
This entity represents the launched data upload process. If the transfer is information about unloading
then run is a running process. Run stores information about the startup time as well as its status.
The user cannot create run himself; It is created as a result of executing transfer.

Example:

.. code-block:: json

    {
        "transfer_id": 123,
        "started_at: "2024-01-19T16:30:07+03:00",
        "ended_at: None,
        "status": "STARTED",
        "log_url: "https://kinaba.url/...",
        "transfer_dump": {
            # transfer object JSON
        },
    }

.. Roles

Roles and rules
===============

- Object within the group can be seen/interacted with only by users which are members of the group.
- Permissions are limited by role assigned to user within specific group.
- There can be only one user in a group with the Owner role, all other roles are not limited in
  number.
- Superuser can read, write to the table and delete without being in the group.

Roles are:

* ``GUEST`` - read-only
* ``DEVELOPER`` - read-write
* ``MAINTAINER`` (DevOps) - read-write + manage queues
* ``OWNER`` (Product Owner) - read-write + manage queues + manage user-group mapping
* ``SUPERUSER`` - meta role assigned to specific users (NOT within group). Read-write + manage queues + manage user-group mapping + create/delete groups.


Groups
-------

.. list-table:: Rights to work with the groups repository.
   :header-rows: 1

   * - Rule \ Role
     - Guest
     - Developer
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
   * - CREATE
     - x
     - x
     - x
     - x
     - x
   * - DELETE
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
     - Developer
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

Transfers, Runs and Connections
--------------------------------

.. list-table:: Right to work wirh Transfers, Runs and Connections repositories.
   :header-rows: 1


   * - Rule \ Role
     - Guest
     - Developer
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

Queues
------

.. list-table:: Rights to read, delete and update queues.
   :header-rows: 1

   * - Rule \ Role
     - Guest
     - Developer
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
