.. _entities:

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
        "username": "user_name",
        "is_superuser": false,
        "is_active": true,
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
        "is_scheduled": false,
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
        "started_at": "2024-01-19T16:30:07+03:00",
        "ended_at": null,
        "status": "STARTED",
        "log_url": "https://kibana.url/...",
        "transfer_dump": {
            "transfer object JSON"
        },
    }

Entity Diagram
--------------

.. plantuml::

    @startuml
    title Entity Diagram

    left to right direction

    entity User {
        * id
        ----
        username
        is_active
        is_superuser
        created_at
        updated_at
        is_deleted
    }

    entity Group {
        * id
        ----
        name
        description
        * owner_id
        created_at
        updated_at
        is_deleted
    }

    entity Connection {
        * id
        ----
        * group_id
        name
        description
        data
        is_deleted
        created_at
        updated_at
    }

    entity Queue {
        * id
        ----
        * group_id
        name
        description
        created_at
        updated_at
        is_deleted
    }

    entity Transfer {
        * id
        ----
        * group_id
        * source_connection_id
        * target_connection_id
        * queue_id
        description
        strategy_params
        source_params
        target_params
        is_scheduled
        schedule
        is_deleted
        created_at
        updated_at
    }

    entity Run {
        * id
        ----
        * transfer_id
        started_at
        ended_at
        status
        log_url
        transfer_dump
        created_at
        updated_at
    }

    Run }o--|| Transfer
    Transfer }o--||Queue
    Transfer }o--|| Connection
    Transfer }o--|| Group
    Connection }o--|{ Group
    Queue }o--|{ Group
    Group }o--o{ User

    @enduml
