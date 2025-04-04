# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from typing import Any

from fastapi import FastAPI

from syncmaster.db.models import User


class AuthProvider(ABC):
    """Basic class for all Auth providers.

    Constructor is called by FastAPI, and can use Dependency injection mechanism.
    See :obj:`~setup` for more details.
    """

    @classmethod
    @abstractmethod
    def setup(cls, app: FastAPI) -> FastAPI:
        """
        This method is called by :obj:`syncmaster.server.application_factory`.

        Here you should add dependency overrides for auth provider,
        and return new ``app`` object.

        Examples
        --------

        .. code-block::

            from fastapi import FastAPI
            from my_awesome_auth_provider.settings import MyAwesomeAuthProviderSettings
            from syncmaster.server.dependencies import Stub

            class MyAwesomeAuthProvider(AuthProvider):
                def setup(app):
                    app.dependency_overrides[AuthProvider] = MyAwesomeAuthProvider

                    # `settings_object_factory` returns MyAwesomeAuthProviderSettings object
                    app.dependency_overrides[MyAwesomeAuthProviderSettings] = settings_object_factory
                    return app

                def __init__(
                    self,
                    settings: Annotated[MyAwesomeAuthProviderSettings, Depends(Stub(MyAwesomeAuthProviderSettings))],
                ):
                    # settings object is set automatically by FastAPI's dependency_overrides
                    self.settings = settings
        """
        ...

    @abstractmethod
    async def get_current_user(self, access_token: Any, *args, **kwargs) -> User:
        """
        This method should return currently logged in user.

        Parameters
        ----------
        access_token : str
            JWT token got from ``Authorization: Bearer <token>`` header.

        Returns
        -------
        :obj:`syncmaster.server.db.models.User`
            Current user object
        """
        ...

    @abstractmethod
    async def get_token_password_grant(
        self,
        grant_type: str | None = None,
        login: str | None = None,
        password: str | None = None,
        scopes: list[str] | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> dict[str, Any]:
        """
        This method should perform authentication and return JWT token.

        Parameters
        ----------
        See:
          * https://auth0.com/docs/get-started/authentication-and-authorization-flow/call-your-api-using-resource-owner-password-flow
          * https://connect2id.com/products/server/docs/api/token

        Returns
        -------
        Dict:
            .. code-block:: python

                {
                    "access_token": "some.jwt.token",
                    "token_type": "bearer",
                    "expires_in": 3600,
                }
        """
        ...

    @abstractmethod
    async def get_token_authorization_code_grant(
        self,
        code: str,
        redirect_uri: str,
        scopes: list[str] | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> dict[str, Any]:
        """
        Obtain a token using the Authorization Code grant.
        """
