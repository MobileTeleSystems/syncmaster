# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from http.client import NO_CONTENT
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

from syncmaster.db.models import User
from syncmaster.errors.registration import get_error_responses
from syncmaster.errors.schemas.invalid_request import InvalidRequestSchema
from syncmaster.errors.schemas.not_authorized import NotAuthorizedSchema
from syncmaster.schemas.v1.auth import AuthTokenSchema
from syncmaster.server.providers.auth import AuthProvider
from syncmaster.server.services.auth import get_auth_provider
from syncmaster.server.services.get_user import get_user
from syncmaster.server.services.unit_of_work import UnitOfWork

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    responses=get_error_responses(include={NotAuthorizedSchema, InvalidRequestSchema}),
)


@router.post("/token")
async def token(
    uow: Annotated[UnitOfWork, Depends()],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_provider: Annotated[AuthProvider, Depends(get_auth_provider)],
) -> AuthTokenSchema:
    token = await auth_provider.get_token_password_grant(
        uow=uow,
        grant_type=form_data.grant_type,
        login=form_data.username,
        password=form_data.password,
        scopes=form_data.scopes,
        client_id=form_data.client_id,
        client_secret=form_data.client_secret,
    )
    return AuthTokenSchema.model_validate(token)


@router.get("/callback", status_code=NO_CONTENT)
async def auth_callback(
    request: Request,
    code: str,
    auth_provider: Annotated[AuthProvider, Depends(get_auth_provider)],
):
    token = await auth_provider.get_token_authorization_code_grant(
        code=code,
        request=request,
    )
    request.session["access_token"] = token["access_token"]
    request.session["refresh_token"] = token["refresh_token"]
    return Response(status_code=NO_CONTENT)


@router.get(
    "/logout",
    summary="Logout user",
    status_code=NO_CONTENT,
)
async def logout(
    request: Request,
    current_user: Annotated[User, Depends(get_user())],
    auth_provider: Annotated[AuthProvider, Depends(get_auth_provider)],
):
    refresh_token = request.session.get("refresh_token", None)
    request.session.clear()
    await auth_provider.logout(user=current_user, refresh_token=refresh_token)
    return Response(status_code=NO_CONTENT)
