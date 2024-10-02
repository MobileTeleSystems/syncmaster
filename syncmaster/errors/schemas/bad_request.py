# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import http

from syncmaster.errors.base import BaseErrorSchema
from syncmaster.errors.registration import register_error_response
from syncmaster.exceptions import SyncmasterError


@register_error_response(
    exception=SyncmasterError,
    status=http.HTTPStatus.BAD_REQUEST,
)
class BadRequestSchema(BaseErrorSchema):
    code: str = "bad_request"
    message: str = "Bad request"
    details: None = None
