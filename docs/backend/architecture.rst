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

        component "LDAP"

        [User] --> [REST API]
        [REST API] --> [Database]
        [REST API] ..> [LDAP]
    @enduml
