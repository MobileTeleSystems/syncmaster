# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Depends, Request
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)

from syncmaster.db.models import User
from syncmaster.exceptions import ActionNotAllowedError, EntityNotFoundError
from syncmaster.server.dependencies import Stub
from syncmaster.server.providers.auth import AuthProvider

bearer_token = HTTPBearer(
    description="Perform authentication using Bearer token",
    auto_error=False,
)
oauth_schema = OAuth2PasswordBearer(
    description="Perform authentication using configured AuthProvider",
    tokenUrl="v1/auth/token",
    auto_error=False,
)


def get_user(  # noqa: WPS231
    is_superuser: bool = False,
) -> Callable[[Request, AuthProvider, str | None, HTTPAuthorizationCredentials | None], Coroutine[Any, Any, User]]:
    async def wrapper(
        request: Request,
        auth_provider: Annotated[AuthProvider, Depends(Stub(AuthProvider))],
        oauth_token: Annotated[str | None, Depends(oauth_schema)],
        bearer_token: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_token)],
    ) -> User:
        access_token: str | None = None
        if bearer_token:
            # explicit token provided by user
            access_token = bearer_token.credentials
        elif oauth_token:
            # DummyAuth stores token in "Authorization" header
            access_token = oauth_token
        elif "session" in request.scope and "access_token" in request.session:
            # KeycloakAuth patches session and store access_token in cookie
            access_token = request.session["access_token"]

        user = await auth_provider.get_current_user(
            access_token=access_token,
            request=request,
        )
        if user is None:
            raise EntityNotFoundError("User not found")
        if not user.is_active:
            raise ActionNotAllowedError("Inactive user")
        if is_superuser and not user.is_superuser:
            raise ActionNotAllowedError("You have no power here")
        return user

    return wrapper
