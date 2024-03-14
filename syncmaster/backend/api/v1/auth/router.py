# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from backend.api.deps import SettingsMarker, UnitOfWorkMarker
from backend.api.v1.auth.utils import sign_jwt
from backend.config import Settings
from backend.services import UnitOfWork
from exceptions import EntityNotFoundError
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from schemas.v1.auth import AuthTokenSchema

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
    except EntityNotFoundError:
        async with unit_of_work:
            user = await unit_of_work.user.create(
                username=form_data.username,
                is_active=True,
            )
    token = sign_jwt(user_id=user.id, settings=settings)
    return AuthTokenSchema(access_token=token, refresh_token="refresh_token")
