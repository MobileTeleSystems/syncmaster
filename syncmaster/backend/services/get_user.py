# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer

from syncmaster.backend.dependencies import Stub
from syncmaster.backend.providers.auth import AuthProvider
from syncmaster.db.models import User
from syncmaster.exceptions.auth import AuthorizationError

oauth_schema = OAuth2PasswordBearer(tokenUrl="v1/auth/token")


def get_user(
    is_active: bool = False,
    is_superuser: bool = False,
) -> Callable[[AuthProvider, str], Coroutine[Any, Any, User]]:
    async def wrapper(
        auth_provider: Annotated[AuthProvider, Depends(Stub(AuthProvider))],
        auth_schema: Annotated[str, Depends(oauth_schema)],
    ) -> User:
        try:
            user = await auth_provider.get_current_user(auth_schema)
        # TODO: replace handling exceptions with get_user to generic handler
        # user is inactive
        except AuthorizationError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if is_active and not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )
        if is_superuser and not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You have no power here",
            )
        return user

    return wrapper
