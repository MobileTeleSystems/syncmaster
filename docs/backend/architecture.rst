.. _backend-architecture:

Architecture
============

.. plantuml::

    @startuml
        title Backend artitecture
        skinparam linetype polyline
        left to right direction

        actor "User"

        frame "SyncMaster" {
            rectangle "Backend" {
                component "REST API"
                database "Database"
                queue "Task Queue"
            }
            rectangle "Workers" {
                collections "Worker"
            }
        }

        database "Data Source"
        database "Data Target"

        [User] --> [REST API]
        [REST API] --> [Database]
        [REST API] --> [Task Queue]

        [Task Queue] --> [Worker]
        [Worker] --> [Database]

        [Worker] --> [Data Source]
        [Worker] --> [Data Target]

    @enduml
