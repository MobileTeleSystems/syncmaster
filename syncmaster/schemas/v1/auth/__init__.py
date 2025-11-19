# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from syncmaster.schemas.v1.auth.basic import (
    CreateBasicAuthSchema,
    ReadBasicAuthSchema,
    UpdateBasicAuthSchema,
)
from syncmaster.schemas.v1.auth.s3 import (
    CreateS3AuthSchema,
    ReadS3AuthSchema,
    UpdateS3AuthSchema,
)
from syncmaster.schemas.v1.auth.samba import (
    CreateSambaAuthSchema,
    ReadSambaAuthSchema,
    UpdateSambaAuthSchema,
)
from syncmaster.schemas.v1.auth.token import AuthTokenSchema, TokenPayloadSchema

__all__ = [
    "CreateBasicAuthSchema",
    "ReadBasicAuthSchema",
    "UpdateBasicAuthSchema",
    "CreateS3AuthSchema",
    "ReadS3AuthSchema",
    "UpdateS3AuthSchema",
    "CreateSambaAuthSchema",
    "ReadSambaAuthSchema",
    "UpdateSambaAuthSchema",
    "AuthTokenSchema",
    "TokenPayloadSchema",
]
