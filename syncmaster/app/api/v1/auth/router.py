from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session
from app.api.v1.auth.schemas import AuthTokenSchema
from app.api.v1.auth.utils import sign_jwt
from app.config import Settings, get_settings
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/token",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings),
) -> AuthTokenSchema:
    """This is test auth method!!! not for production!!!!"""
    user = (
        (await session.execute(select(User).filter_by(username=form_data.username)))
        .scalars()
        .first()
    )
    if user is None:
        user = User(username=form_data.username, is_active=True)  # type: ignore
        session.add(user)
        await session.commit()
        await session.refresh(user)

    token = sign_jwt(user_id=user.id, settings=settings)
    return AuthTokenSchema(access_token=token, refresh_token="refresh_token")
