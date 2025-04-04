# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from http.client import NOT_FOUND
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from syncmaster.errors.registration import get_error_responses
from syncmaster.errors.schemas.invalid_request import InvalidRequestSchema
from syncmaster.errors.schemas.not_authorized import NotAuthorizedSchema
from syncmaster.schemas.v1.auth import AuthTokenSchema
from syncmaster.server.dependencies import Stub
from syncmaster.server.providers.auth import (
    AuthProvider,
    DummyAuthProvider,
    KeycloakAuthProvider,
)
from syncmaster.server.utils.state import validate_state

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    responses=get_error_responses(include={NotAuthorizedSchema, InvalidRequestSchema}),
)


@router.post("/token")
async def token(
    auth_provider: Annotated[DummyAuthProvider, Depends(Stub(AuthProvider))],
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> AuthTokenSchema:
    token = await auth_provider.get_token_password_grant(
        grant_type=form_data.grant_type,
        login=form_data.username,
        password=form_data.password,
        scopes=form_data.scopes,
        client_id=form_data.client_id,
        client_secret=form_data.client_secret,
    )
    return AuthTokenSchema.model_validate(token)


@router.get("/callback")
async def auth_callback(
    request: Request,
    code: str,
    state: str,
    auth_provider: Annotated[KeycloakAuthProvider, Depends(Stub(AuthProvider))],
):
    original_redirect_url = validate_state(state)
    if not original_redirect_url:
        raise HTTPException(status_code=NOT_FOUND, detail="Invalid state parameter")
    token = await auth_provider.get_token_authorization_code_grant(
        code=code,
        redirect_uri=auth_provider.settings.keycloak.redirect_uri,
    )
    request.session["access_token"] = token["access_token"]
    request.session["refresh_token"] = token["refresh_token"]

    return RedirectResponse(url=original_redirect_url)
