# SPDX-FileCopyrightText: 2025-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import logging
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Request
from keycloak import KeycloakOpenID, KeycloakOperationError

from syncmaster.db.models import User
from syncmaster.exceptions import EntityNotFoundError
from syncmaster.exceptions.auth import AuthorizationError
from syncmaster.server.dependencies import Stub
from syncmaster.server.providers.auth.base_provider import AuthProvider
from syncmaster.server.services.unit_of_work import UnitOfWork
from syncmaster.server.settings.auth.oauth2_gateway import OAuth2GatewayProviderSettings

log = logging.getLogger(__name__)


class OAuth2GatewayProvider(AuthProvider):
    def __init__(  # noqa: WPS612
        self,
        settings: Annotated[OAuth2GatewayProviderSettings, Depends(Stub(OAuth2GatewayProviderSettings))],
        unit_of_work: Annotated[UnitOfWork, Depends()],
    ) -> None:
        self.settings = settings
        self._uow = unit_of_work
        self.keycloak_openid = KeycloakOpenID(
            server_url=str(self.settings.keycloak.api_url).rstrip("/") + "/",  # noqa: WPS336
            client_id=self.settings.keycloak.client_id,
            realm_name=self.settings.keycloak.realm_name,
            client_secret_key=self.settings.keycloak.client_secret.get_secret_value(),
            verify=self.settings.keycloak.verify_ssl,
        )

    @classmethod
    def setup(cls, app: FastAPI) -> FastAPI:
        settings = OAuth2GatewayProviderSettings.model_validate(
            app.state.settings.auth.model_dump(exclude={"provider"}),
        )
        log.info("Using %s provider with settings:\n%s", cls.__name__, settings)
        app.dependency_overrides[AuthProvider] = cls
        app.dependency_overrides[OAuth2GatewayProviderSettings] = lambda: settings
        return app

    async def get_current_user(  # noqa: WPS231, WPS217, WPS238
        self,
        access_token: str | None,
        request: Request,
    ) -> User:
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
        login = token_info.get("preferred_username")
        if not login:
            raise AuthorizationError("Invalid token")

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

    async def get_token_password_grant(
        self,
        grant_type: str | None = None,
        login: str | None = None,
        password: str | None = None,
        scopes: list[str] | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError(
            f"Password grant is not supported by {self.__class__.__name__}.",  # noqa: WPS237
        )

    async def get_token_authorization_code_grant(
        self,
        code: str,
        scopes: list[str] | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError(
            f"Authorization code grant is not supported by {self.__class__.__name__}.",  # noqa: WPS237
        )

    async def logout(self, user: User, refresh_token: str | None) -> None:
        raise NotImplementedError(
            f"Logout is not supported by {self.__class__.__name__}.",  # noqa: WPS237
        )
