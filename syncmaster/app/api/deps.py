from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.v1.auth.utils import decode_jwt, oauth2_scheme
from app.config import Settings, get_settings
from app.db.models import User


async def get_async_sessionmaker(settings: Settings = Depends(get_settings)):
    engine = create_async_engine(settings.DATABASE_URI, echo=False)  # type: ignore
    return async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )


async def get_async_session(
    async_session: async_sessionmaker[AsyncSession] = Depends(get_async_sessionmaker),
) -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def get_current_user(
    session: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> User:
    token_data = decode_jwt(token, settings=settings)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="You are not authorized"
        )
    user = await session.get(User, token_data.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active or current_user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return current_user


async def get_superuser(current_user: User = Depends(get_current_user)):
    if not current_user.is_superuser or current_user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You have no power here"
        )
    return current_user
