.. _backend-auth-ldap:

KeyCloak Auth provider
==================

Description
-----------

TODO:

Strategies
----------

TODO:

Interaction schema
------------------

.. dropdown:: Interaction schema

    .. plantuml::

        @startuml
            title Keycloak Authorization Flow
            participant "Client (User from Browser)" as Client
            participant "Syncmaster"
            participant "Keycloak"

            == Client Authentication at Keycloak ==
            Client -> Syncmaster : Request endpoint that requires authentication (/v1/users)

            Syncmaster x-[#red]> Client : Redirect to Keycloak login URL (if no access token)

            Client -> Keycloak : Callback redirect to Keycloak login page

            alt Successful login
                Client --> Keycloak : Log in with login and password
            else Login failed
                Keycloak x-[#red]> Client -- : Display error (401 Unauthorized)
            end

            Keycloak -> Client : Redirect to Syncmaster to callback endpoint with code
            Client -> Syncmaster : Callback request to /v1/auth/callback with code
            Syncmaster-> Keycloak : Exchange code for access token
            Keycloak --> Syncmaster : Return JWT token
            Syncmaster --> Client : Set JWT token in user's browser in cookies and redirect /v1/users

            Client --> Syncmaster : Redirect to /v1/users
            Syncmaster -> Syncmaster : Get user info from JWT token and check user in internal backend database
            Syncmaster -> Syncmaster : Create user in internal backend database if not exist
            Syncmaster -[#green]> Client -- : Return requested data



            == GET v1/users ==
            alt Successful case
                Client -> Syncmaster : Request data with JWT token
                Syncmaster --> Syncmaster : Get user info from JWT token and check user in internal backend database
                Syncmaster -> Syncmaster : Create user in internal backend database if not exist
                Syncmaster -[#green]> Client -- : Return requested data

            else Access token is expired
                Syncmaster -> Keycloak : Get new JWT token via refresh token
                Keycloak --> Syncmaster : Return new JWT token
                Syncmaster --> Syncmaster : Get user info from JWT token and check user in internal backend database
                Syncmaster -> Syncmaster : Create user in internal backend database if not exist
                Syncmaster -[#green]> Client -- : Return requested data and set new JWT token in user's browser in cookies

            else Refresh token is expired
                Syncmaster x-[#red]> Client -- : Redirect to Keycloak login URL
            end

            deactivate Client
        @enduml

Basic configuration
-------------------

.. autopydantic_model:: syncmaster.settings.auth.keycloak.KeycloakProviderSettings
.. autopydantic_model:: syncmaster.settings.auth.jwt.JWTSettings

