.. _server-auth-dummy:

Dummy Auth provider
===================

Description
-----------

This auth provider allows to sign-in with any username and password, and and then issues an access token.

After successful auth, username is saved to server database. It is then used for creating audit records for any object change, see ``changed_by`` field.

Interaction schema
------------------

.. dropdown:: Interaction schema

    .. plantuml::

        @startuml
            title DummyAuthProvider
            participant "Client"
            participant "Server"

            == POST v1/auth/token ==

            activate "Client"
            alt Successful case
                "Client" -> "Server" ++ : login + password
                "Server" --> "Server" : Password is completely ignored
                "Server" --> "Server" : Check user in internal server database
                "Server" -> "Server" : Create user if not exist
                "Server" -[#green]> "Client" -- : Generate and return access_token

            else User is blocked
                "Client" -> "Server" ++ : login + password
                "Server" --> "Server" : Password is completely ignored
                "Server" --> "Server" : Check user in internal server database
                "Server" x-[#red]> "Client" -- : 401 Unauthorized

            else User is deleted
                "Client" -> "Server" ++ : login + password
                "Server" --> "Server" : Password is completely ignored
                "Server" --> "Server" : Check user in internal server database
                "Server" x-[#red]> "Client" -- : 404 Not found
            end

            == GET v1/namespaces ==

            alt Successful case
                "Client" -> "Server" ++ : access_token
                "Server" --> "Server" : Validate token
                "Server" --> "Server" : Check user in internal server database
                "Server" -> "Server" : Get data
                "Server" -[#green]> "Client" -- : Return data

            else Token is expired
                "Client" -> "Server" ++ : access_token
                "Server" --> "Server" : Validate token
                "Server" x-[#red]> "Client" -- : 401 Unauthorized

            else User is blocked
                "Client" -> "Server" ++ : access_token
                "Server" --> "Server" : Validate token
                "Server" --> "Server" : Check user in internal server database
                "Server" x-[#red]> "Client" -- : 401 Unauthorized

            else User is deleted
                "Client" -> "Server" ++ : access_token
                "Server" --> "Server" : Validate token
                "Server" --> "Server" : Check user in internal server database
                "Server" x-[#red]> "Client" -- : 404 Not found
            end

            deactivate "Client"
        @enduml

Configuration
-------------

.. autopydantic_model:: syncmaster.server.settings.auth.dummy.DummyAuthProviderSettings
.. autopydantic_model:: syncmaster.server.settings.auth.jwt.JWTSettings
