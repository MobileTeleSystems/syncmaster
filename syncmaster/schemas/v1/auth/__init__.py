# SPDX-FileCopyrightText: 2023-present MTS PJSC
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
    "AuthTokenSchema",
    "CreateBasicAuthSchema",
    "CreateS3AuthSchema",
    "CreateSambaAuthSchema",
    "ReadBasicAuthSchema",
    "ReadS3AuthSchema",
    "ReadSambaAuthSchema",
    "TokenPayloadSchema",
    "UpdateBasicAuthSchema",
    "UpdateS3AuthSchema",
    "UpdateSambaAuthSchema",
]
