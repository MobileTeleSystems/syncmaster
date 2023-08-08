from collections.abc import Awaitable, Callable

from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.api.deps import AuthMarker, DatabaseProviderMarker, SettingsMarker
from app.api.v1.auth.utils import decode_jwt
from app.config import Settings
from app.db.models import User
from app.db.provider import DatabaseProvider


def get_user(
    is_active: bool = False,
    is_superuser: bool = False,
) -> Callable[[str, Settings, DatabaseProvider], Awaitable[User]]:
    async def wrapper(
        token: str = Depends(AuthMarker),
        settings: Settings = Depends(SettingsMarker),
        provider: DatabaseProvider = Depends(DatabaseProviderMarker),
    ) -> User:
        token_data = decode_jwt(token, settings=settings)
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized",
            )
        user = await provider.user.read_by_id(user_id=token_data.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if is_active and not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
            )
        if is_superuser and not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You have no power here"
            )
        return user

    return wrapper


def get_auth_scheme(
    settings: Settings,
) -> Callable[[Request], str] | OAuth2PasswordBearer:
    if settings.DEBUG:
        return OAuth2PasswordBearer(tokenUrl=settings.AUTH_TOKEN_URL)
    return lambda request: "Here will be keycloak"
