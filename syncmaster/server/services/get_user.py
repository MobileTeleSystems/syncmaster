# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer

from syncmaster.db.models import User
from syncmaster.exceptions import ActionNotAllowedError, EntityNotFoundError
from syncmaster.server.dependencies import Stub
from syncmaster.server.providers.auth import AuthProvider

oauth_schema = OAuth2PasswordBearer(tokenUrl="v1/auth/token", auto_error=False)


def get_user(
    is_active: bool = False,
    is_superuser: bool = False,
) -> Callable[[Request, AuthProvider, str], Coroutine[Any, Any, User]]:
    async def wrapper(
        request: Request,
        auth_provider: Annotated[AuthProvider, Depends(Stub(AuthProvider))],
        access_token: Annotated[str | None, Depends(oauth_schema)],
    ) -> User:
        # keycloak provider patches session and store access_token in cookie,
        # when dummy auth stores it in "Authorization" header
        access_token = request.session.get("access_token", "") or access_token
        user = await auth_provider.get_current_user(
            access_token=access_token,
            request=request,
        )
        if user is None:
            raise EntityNotFoundError("User not found")
        if is_active and not user.is_active:
            raise ActionNotAllowedError("Inactive user")
        if is_superuser and not user.is_superuser:
            raise ActionNotAllowedError("You have no power here")
        return user

    return wrapper
