# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from syncmaster.backend.api.v1.auth.utils import sign_jwt
from syncmaster.backend.dependencies import Stub
from syncmaster.backend.services import UnitOfWork
from syncmaster.errors.registration import get_error_responses
from syncmaster.errors.schemas.invalid_request import InvalidRequestSchema
from syncmaster.errors.schemas.not_authorized import NotAuthorizedSchema
from syncmaster.exceptions import EntityNotFoundError
from syncmaster.schemas.v1.auth import AuthTokenSchema
from syncmaster.settings import Settings

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    responses=get_error_responses(include={NotAuthorizedSchema, InvalidRequestSchema}),
)


@router.post("/token")
async def login(
    settings: Annotated[Settings, Depends(Stub(Settings))],
    form_data: OAuth2PasswordRequestForm = Depends(),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
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
