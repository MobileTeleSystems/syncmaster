# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from typing import Any

from fastapi import FastAPI, Request

from syncmaster.db.models import User
from syncmaster.server.services.unit_of_work import UnitOfWork


class AuthProvider(ABC):
    """Basic class for all Auth providers.

    Constructor is called by FastAPI, and can use Dependency injection mechanism.
    See [setup][syncmaster.server.providers.auth.AuthProvider.setup] for more details.
    """

    @classmethod
    @abstractmethod
    def setup(cls, app: FastAPI) -> FastAPI:
        """
        This method is called by `application_factory`.

        Here you should configure your auth provider, set `app.state.auth_provider`
        and return new `app` object.

        Examples
        --------

        ```python
        from fastapi import FastAPI
        from my_awesome_auth_provider.settings import MyAwesomeAuthProviderSettings

        class MyAwesomeAuthProvider(AuthProvider):
            def setup(app):
                settings_dict = app.state.settings.auth.model_dump(exclude={"provider})
                settings = MyAwesomeAuthProviderSettings.model_validate(settings_dict)
                app.state.auth_provider = MyAwesomeAuthProvider(settings)
                return app

            def __init__(
                self,
                settings: MyAwesomeAuthProviderSettings,
            ):
                self.settings = settings
        ```
        """
        ...

    @abstractmethod
    async def get_current_user(self, access_token: str | None, request: Request, uow: UnitOfWork) -> User:
        """
        This method should return currently logged in user.

        Parameters
        ----------
        access_token : str
            JWT token got from `Authorization: Bearer <token>` header.

        Returns
        -------
        syncmaster.db.models.User
            Current user object
        """
        ...

    @abstractmethod
    async def get_token_password_grant(  # noqa: PLR0913, PLR0917
        self,
        uow: UnitOfWork,
        grant_type: str | None = None,
        login: str | None = None,
        password: str | None = None,
        scopes: list[str] | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> dict[str, Any]:
        """
        This method should perform authentication and return JWT token.

        Parameters are described in:

        * <https://auth0.com/docs/get-started/authentication-and-authorization-flow/call-your-api-using-resource-owner-password-flow>
        * <https://connect2id.com/products/server/docs/api/token>

        Returns
        -------
        Dict:
            ```python
            {
                "access_token": "some.jwt.token",
                "token_type": "bearer",
                "expires_in": 3600,
            }
            ```
        """
        ...

    @abstractmethod
    async def get_token_authorization_code_grant(
        self,
        code: str,
        request: Request,
        scopes: list[str] | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> dict[str, Any]:
        """
        Obtain a token using the Authorization Code grant.
        """

    @abstractmethod
    async def logout(self, user: User, refresh_token: str | None) -> None:
        """
        Logout user
        """
