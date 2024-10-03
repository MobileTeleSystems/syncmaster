# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from syncmaster.errors.base import BaseErrorSchema
from syncmaster.errors.registration import (
    APIErrorResponse,
    get_error_responses,
    get_response_for_exception,
    get_response_for_status_code,
)

__all__ = [
    "APIErrorResponse",
    "BaseErrorSchema",
    "get_error_responses",
    "get_response_for_exception",
    "get_response_for_status_code",
]
