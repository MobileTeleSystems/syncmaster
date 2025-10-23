# KeyCloak Auth provider { #keycloak-auth-provider }

## Description { #keycloak-auth-provider-description }

Keycloak auth provider uses [python-keycloak](https://pypi.org/project/python-keycloak/) library to interact with Keycloak server. During the authentication process,
KeycloakAuthProvider redirects user to Keycloak authentication page.

After successful authentication, Keycloak redirects user back to Syncmaster with authorization code.
Then KeycloakAuthProvider exchanges authorization code for an access token and uses it to get user information from Keycloak server.
If user is not found in Syncmaster database, KeycloakAuthProvider creates it. Finally, KeycloakAuthProvider returns user with access token.

You can follow interaction schema below.

## Interaction schema { #keycloak-auth-provider-interaction-schema }

```plantuml

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
            Syncmaster -> Syncmaster : Get user info from JWT token and check user in internal server database
            Syncmaster -> Syncmaster : Create user in internal server database if not exist
            Syncmaster -[#green]> Client -- : Return requested data



            == GET v1/users ==
            alt Successful case
                Client -> Syncmaster : Request data with JWT token
                Syncmaster --> Syncmaster : Get user info from JWT token and check user in internal server database
                Syncmaster -> Syncmaster : Create user in internal server database if not exist
                Syncmaster -[#green]> Client -- : Return requested data

            else Access token is expired
                Syncmaster -> Keycloak : Get new JWT token via refresh token
                Keycloak --> Syncmaster : Return new JWT token
                Syncmaster --> Syncmaster : Get user info from JWT token and check user in internal server database
                Syncmaster -> Syncmaster : Create user in internal server database if not exist
                Syncmaster -[#green]> Client -- : Return requested data and set new JWT token in user's browser in cookies

            else Refresh token is expired
                Syncmaster x-[#red]> Client -- : Redirect to Keycloak login URL
            end

            deactivate Client
        @enduml
```

## Basic configuration { #keycloak-auth-provider-basic-configuration }

::: syncmaster.server.settings.auth.keycloak.KeycloakAuthProviderSettings

::: syncmaster.server.settings.auth.keycloak.KeycloakSettings

::: syncmaster.server.settings.auth.jwt.JWTSettings

## Keycloak

- [Local installation][local_installation]
