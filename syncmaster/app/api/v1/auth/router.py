from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import SettingsMarker, UnitOfWorkMarker
from app.api.services.unit_of_work import UnitOfWork
from app.api.v1.auth.schemas import AuthTokenSchema
from app.api.v1.auth.utils import sign_jwt
from app.config import Settings
from app.exceptions import EntityNotFound

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
    settings: Settings = Depends(SettingsMarker),
) -> AuthTokenSchema:
    """This is the test auth method!!! Not for production!!!!"""
    try:
        user = await unit_of_work.user.read_by_username(username=form_data.username)
    except EntityNotFound:
        async with unit_of_work:
            user = await unit_of_work.user.create(
                username=form_data.username,
                is_active=True,
            )
    token = sign_jwt(user_id=user.id, settings=settings)
    return AuthTokenSchema(access_token=token, refresh_token="refresh_token")
