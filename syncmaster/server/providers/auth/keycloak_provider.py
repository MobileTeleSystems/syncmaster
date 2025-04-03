# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import logging
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Request
from keycloak import KeycloakOpenID

from syncmaster.exceptions import EntityNotFoundError
from syncmaster.exceptions.auth import AuthorizationError
from syncmaster.exceptions.redirect import RedirectException
from syncmaster.server.dependencies import Stub
from syncmaster.server.providers.auth.base_provider import AuthProvider
from syncmaster.server.services.unit_of_work import UnitOfWork
from syncmaster.server.settings.auth.keycloak import KeycloakAuthProviderSettings
from syncmaster.server.utils.state import generate_state

log = logging.getLogger(__name__)


class KeycloakAuthProvider(AuthProvider):
    def __init__(
        self,
        settings: Annotated[KeycloakAuthProviderSettings, Depends(Stub(KeycloakAuthProviderSettings))],
        unit_of_work: Annotated[UnitOfWork, Depends()],
    ) -> None:
        self.settings = settings
        self._uow = unit_of_work
        self.keycloak_openid = KeycloakOpenID(
            server_url=self.settings.keycloak.server_url,
            client_id=self.settings.keycloak.client_id,
            realm_name=self.settings.keycloak.realm_name,
            client_secret_key=self.settings.keycloak.client_secret.get_secret_value(),
            verify=self.settings.keycloak.verify_ssl,
        )

    @classmethod
    def setup(cls, app: FastAPI) -> FastAPI:
        settings = KeycloakAuthProviderSettings.model_validate(app.state.settings.auth.model_dump(exclude={"provider"}))
        log.info("Using %s provider with settings:\n%s", cls.__name__, settings)
        app.dependency_overrides[AuthProvider] = cls
        app.dependency_overrides[KeycloakAuthProviderSettings] = lambda: settings
        return app

    async def get_token_password_grant(
        self,
        grant_type: str | None = None,
        login: str | None = None,
        password: str | None = None,
        scopes: list[str] | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError("Password grant is not supported by KeycloakAuthProvider.")

    async def get_token_authorization_code_grant(
        self,
        code: str,
        redirect_uri: str,
        scopes: list[str] | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> dict[str, Any]:
        try:
            redirect_uri = redirect_uri or self.settings.keycloak.redirect_uri
            token = self.keycloak_openid.token(
                grant_type="authorization_code",
                code=code,
                redirect_uri=redirect_uri,
            )
            return token
        except Exception as e:
            raise AuthorizationError("Failed to get token") from e

    async def get_current_user(self, access_token: str, *args, **kwargs) -> Any:  # noqa: WPS231
        request: Request = kwargs["request"]
        refresh_token = request.session.get("refresh_token")

        if not access_token:
            log.debug("No access token found in session.")
            self.redirect_to_auth(request.url.path)

        try:
            # if user is disabled or blocked in Keycloak after the token is issued, he will
            # remain authorized until the token expires (not more than 15 minutes in MTS SSO)
            token_info = self.keycloak_openid.decode_token(token=access_token)
        except Exception as e:
            log.info("Access token is invalid or expired: %s", e)
            token_info = None

        if not token_info and refresh_token:
            log.debug("Access token invalid. Attempting to refresh.")

            try:
                new_tokens = await self.refresh_access_token(refresh_token)

                new_access_token = new_tokens["access_token"]
                new_refresh_token = new_tokens["refresh_token"]
                request.session["access_token"] = new_access_token
                request.session["refresh_token"] = new_refresh_token

                token_info = self.keycloak_openid.decode_token(
                    token=new_access_token,
                )
                log.debug("Access token refreshed and decoded successfully.")
            except Exception as e:
                log.debug("Failed to refresh access token: %s", e)
                self.redirect_to_auth(request.url.path)

        if not token_info:
            raise AuthorizationError("Invalid token payload")

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

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        new_tokens = self.keycloak_openid.refresh_token(refresh_token)
        return new_tokens

    def redirect_to_auth(self, path: str) -> None:
        state = generate_state(path)
        auth_url = self.keycloak_openid.auth_url(
            redirect_uri=self.settings.keycloak.redirect_uri,
            scope=self.settings.keycloak.scope,
            state=state,
        )
        raise RedirectException(redirect_url=auth_url)
