# SPDX-FileCopyrightText: 2023-present MTS PJSC
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
from syncmaster.server.providers.auth import AuthProvider
from syncmaster.server.services.auth import get_auth_provider
from syncmaster.server.services.unit_of_work import UnitOfWork

bearer_token = HTTPBearer(
    description="Perform authentication using Bearer token",
    auto_error=False,
)
oauth_schema = OAuth2PasswordBearer(
    description="Perform authentication using configured AuthProvider",
    tokenUrl="v1/auth/token",
    auto_error=False,
)


def get_user(
    is_superuser: bool = False,  # noqa: FBT001, FBT002
) -> Callable[
    [Request, AuthProvider, str | None, HTTPAuthorizationCredentials | None, UnitOfWork],
    Coroutine[Any, Any, User],
]:
    async def wrapper(
        request: Request,
        auth_provider: Annotated[AuthProvider, Depends(get_auth_provider)],
        oauth_token: Annotated[str | None, Depends(oauth_schema)],
        bearer_token: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_token)],
        uow: Annotated[UnitOfWork, Depends()],
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
            uow=uow,
        )
        if user is None:
            msg = "User not found"
            raise EntityNotFoundError(msg)
        if not user.is_active:
            msg = "Inactive user"
            raise ActionNotAllowedError(msg)
        if is_superuser and not user.is_superuser:
            msg = "You have no power here"
            raise ActionNotAllowedError(msg)
        return user

    return wrapper
