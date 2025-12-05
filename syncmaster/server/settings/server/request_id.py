# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

import textwrap

from pydantic import BaseModel, Field


class RequestIDSettings(BaseModel):
    """X-Request-ID Middleware Settings.

    See `asgi-correlation-id <https://github.com/snok/asgi-correlation-id>`_ documentation.

    Examples
    --------

    .. code-block:: yaml
        :caption: config.yml

        server:
            request_id:
                enabled: True
                header_name: X-Request-ID
                update_request_header: True
    """

    enabled: bool = Field(default=True, description="Set to ``True`` to enable middleware")
    header_name: str = Field(
        default="X-Request-ID",
        description="Name of response header which is filled up with request ID value",
    )
    update_request_header: bool = Field(
        default=False,
        description=textwrap.dedent(
            """
            If ``False``, bypass header value from request to response as-is.

            If ``True``, always set new value of specific header.
            """,
        ),
    )
