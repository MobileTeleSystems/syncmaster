.. _backend-architecture:

Architecture
============

.. plantuml::

    @startuml
        title Backend artitecture
        skinparam linetype polyline
        left to right direction

        actor "User"

        frame "Syncmaster" {
            component "REST API"
            database "Database"
        }

        frame "Worker node" {
            component "Worker"
            component "Spark Session"
        }

        database "Source"
        database "Target"

        component "Queue"

        [User] --> [REST API]
        [REST API] --> [Database]
        [REST API] ..> [Queue]
        [Worker] ..> [Queue]
        [Worker] ..> [Database]
        [Spark Session] ..> [Source]
        [Spark Session] ..> [Target]

    @enduml
