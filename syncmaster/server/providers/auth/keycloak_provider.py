# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import logging
from typing import Annotated, Any, NoReturn

from fastapi import Depends, FastAPI, Request
from jwcrypto.common import JWException
from keycloak import KeycloakOpenID, KeycloakOperationError
from starlette.middleware.sessions import SessionMiddleware

from syncmaster.db.models.user import User
from syncmaster.exceptions import EntityNotFoundError
from syncmaster.exceptions.auth import AuthorizationError, LogoutError
from syncmaster.exceptions.redirect import RedirectException
from syncmaster.server.dependencies import Stub
from syncmaster.server.providers.auth.base_provider import AuthProvider
from syncmaster.server.services.unit_of_work import UnitOfWork
from syncmaster.server.settings.auth.keycloak import KeycloakAuthProviderSettings

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
            server_url=str(self.settings.keycloak.api_url).rstrip("/") + "/",  # noqa: WPS336
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

        app.add_middleware(
            SessionMiddleware,
            secret_key=settings.cookie.secret_key.get_secret_value(),
            session_cookie=settings.cookie.name,
            max_age=settings.cookie.max_age,
            path=settings.cookie.path,
            same_site=settings.cookie.same_site,
            https_only=settings.cookie.https_only,
            domain=settings.cookie.domain,
        )
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
        try:
            return await self.keycloak_openid.a_token(
                grant_type="authorization_code",
                code=code,
                redirect_uri=self.settings.keycloak.ui_callback_url,
            )
        except KeycloakOperationError as e:
            raise AuthorizationError("Failed to get token") from e

    async def get_current_user(self, access_token: str | None, request: Request) -> User:  # noqa: WPS231, WPS217
        if not access_token:
            log.debug("No access token found in session")
            await self.redirect_to_auth()

        refresh_token = request.session.get("refresh_token")
        try:
            # if user is disabled or blocked in Keycloak after the token is issued, he will
            # remain authorized until the token expires (not more than 15 minutes in MTS SSO)
            token_info = await self.keycloak_openid.a_decode_token(access_token)
        except (KeycloakOperationError, JWException) as e:
            log.info("Access token is invalid or expired: %s", e)
            token_info = None

        if not token_info and refresh_token:
            log.debug("Access token invalid. Attempting to refresh.")

            try:
                new_tokens = await self.keycloak_openid.a_refresh_token(refresh_token)

                new_access_token = new_tokens["access_token"]
                new_refresh_token = new_tokens["refresh_token"]
                request.session["access_token"] = new_access_token
                request.session["refresh_token"] = new_refresh_token

                token_info = await self.keycloak_openid.a_decode_token(
                    token=new_access_token,
                )
                log.debug("Access token refreshed and decoded successfully.")
            except (KeycloakOperationError, JWException) as e:
                log.debug("Failed to refresh access token: %s", e)
                await self.redirect_to_auth()

        if not token_info:
            raise AuthorizationError("Invalid token payload")

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

    async def redirect_to_auth(self) -> NoReturn:
        auth_url = await self.keycloak_openid.a_auth_url(
            redirect_uri=self.settings.keycloak.ui_callback_url,
            scope=self.settings.keycloak.scope,
        )
        raise RedirectException(redirect_url=auth_url)

    async def logout(self, user: User, refresh_token: str | None) -> None:
        if not refresh_token:
            log.debug("No refresh token found in session.")
            return

        try:
            await self.keycloak_openid.a_logout(refresh_token)
        except KeycloakOperationError as err:
            msg = f"Can't logout user: {user.username}"
            log.debug("%s. Error: %s", msg, err)
            raise LogoutError(msg) from err
