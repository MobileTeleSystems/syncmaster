# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from syncmaster.backend.dependencies import Stub
from syncmaster.backend.providers.auth import AuthProvider
from syncmaster.errors.registration import get_error_responses
from syncmaster.errors.schemas.invalid_request import InvalidRequestSchema
from syncmaster.errors.schemas.not_authorized import NotAuthorizedSchema
from syncmaster.schemas.v1.auth import AuthTokenSchema

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    responses=get_error_responses(include={NotAuthorizedSchema, InvalidRequestSchema}),
)


@router.post("/token")
async def login(
    auth_provider: Annotated[AuthProvider, Depends(Stub(AuthProvider))],
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> AuthTokenSchema:
    token = await auth_provider.get_token(
        grant_type=form_data.grant_type,
        login=form_data.username,
        password=form_data.password,
        scopes=form_data.scopes,
        client_id=form_data.client_id,
        client_secret=form_data.client_secret,
    )
    return AuthTokenSchema.parse_obj(token)
