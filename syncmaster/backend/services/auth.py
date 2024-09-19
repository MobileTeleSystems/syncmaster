# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Awaitable, Callable

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer

from syncmaster.backend.api.deps import SettingsMarker, UnitOfWorkMarker
from syncmaster.backend.api.v1.auth.utils import decode_jwt
from syncmaster.backend.services.unit_of_work import UnitOfWork
from syncmaster.config import Settings
from syncmaster.db.models import User

oauth_schema = OAuth2PasswordBearer(tokenUrl="v1/auth/token")


def get_user(
    is_active: bool = False,
    is_superuser: bool = False,
) -> Callable[[str, Settings, UnitOfWork], Awaitable[User]]:
    async def wrapper(
        token: str = Depends(oauth_schema),
        settings: Settings = Depends(SettingsMarker),
        unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
    ) -> User:
        async with unit_of_work:
            token_data = decode_jwt(token, settings=settings)
            if token_data is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="You are not authorized",
                )
            user = await unit_of_work.user.read_by_id(user_id=token_data.user_id)
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
