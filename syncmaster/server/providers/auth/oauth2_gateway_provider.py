# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import logging
from typing import Any

from fastapi import Request

from syncmaster.db.models import User
from syncmaster.exceptions import EntityNotFoundError
from syncmaster.exceptions.auth import AuthorizationError
from syncmaster.server.providers.auth.keycloak_provider import (
    KeycloakAuthProvider,
    KeycloakOperationError,
)

log = logging.getLogger(__name__)


class OAuth2GatewayProvider(KeycloakAuthProvider):
    async def get_current_user(self, access_token: str | None, request: Request) -> User:  # noqa: WPS231, WPS217

        if not access_token:
            log.debug("No access token found in request")
            raise AuthorizationError("Missing auth credentials")

        try:
            token_info = await self.keycloak_openid.a_introspect(access_token)
        except KeycloakOperationError as e:
            log.info("Failed to introspect token: %s", e)
            raise AuthorizationError("Invalid token payload")

        if token_info["active"] is False:
            raise AuthorizationError("Token is not active")

        # these names are hardcoded in keycloak:
        # https://github.com/keycloak/keycloak/blob/3ca3a4ad349b4d457f6829eaf2ae05f1e01408be/core/src/main/java/org/keycloak/representations/IDToken.java
        # TODO: make sure which fields are guaranteed
        login = token_info["preferred_username"]
        email = token_info.get("email")
        first_name = token_info.get("given_name")
        middle_name = token_info.get("middle_name")
        last_name = token_info.get("family_name")

        async with self._uow:
            try:
                user = await self._uow.user.read_by_username(login)
            except EntityNotFoundError:
                user = await self._uow.user.create(
                    username=login,
                    email=email,
                    first_name=first_name,
                    middle_name=middle_name,
                    last_name=last_name,
                )
        return user

    async def get_token_authorization_code_grant(
        self,
        code: str,
        scopes: list[str] | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError(f"Authorization code grant is not supported by {self.__class__.__name__}.")

    async def logout(self, user: User, refresh_token: str | None) -> None:
        raise NotImplementedError(f"Logout is not supported by {self.__class__.__name__}.")
