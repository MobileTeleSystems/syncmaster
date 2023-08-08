from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DatabaseProviderMarker, SettingsMarker
from app.api.v1.auth.schemas import AuthTokenSchema
from app.api.v1.auth.utils import sign_jwt
from app.config import Settings
from app.db.provider import DatabaseProvider
from app.exceptions import EntityNotFound

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
    settings: Settings = Depends(SettingsMarker),
) -> AuthTokenSchema:
    """This is test auth method!!! not for production!!!!"""
    try:
        user = await provider.user.read_by_username(username=form_data.username)
    except EntityNotFound:
        user = await provider.user.create(username=form_data.username, is_active=True)
    token = sign_jwt(user_id=user.id, settings=settings)
    return AuthTokenSchema(access_token=token, refresh_token="refresh_token")
