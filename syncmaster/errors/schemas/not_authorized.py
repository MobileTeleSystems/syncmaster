# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import http
from typing import Any, Literal

from syncmaster.errors.base import BaseErrorSchema
from syncmaster.errors.registration import register_error_response
from syncmaster.exceptions.auth import AuthorizationError


@register_error_response(
    exception=AuthorizationError,
    status=http.HTTPStatus.UNAUTHORIZED,
)
class NotAuthorizedSchema(BaseErrorSchema):
    code: Literal["unauthorized"] = "unauthorized"
    details: Any = None
