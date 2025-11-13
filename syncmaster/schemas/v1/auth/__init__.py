# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from syncmaster.schemas.v1.auth.basic import (
    BasicAuthSchema,
    CreateBasicAuthSchema,
    ReadBasicAuthSchema,
    UpdateBasicAuthSchema,
)
from syncmaster.schemas.v1.auth.s3 import (
    CreateS3AuthSchema,
    ReadS3AuthSchema,
    S3AuthSchema,
    UpdateS3AuthSchema,
)
from syncmaster.schemas.v1.auth.samba import (
    CreateSambaAuthSchema,
    ReadSambaAuthSchema,
    SambaAuthSchema,
    UpdateSambaAuthSchema,
)
from syncmaster.schemas.v1.auth.token import AuthTokenSchema, TokenPayloadSchema

__all__ = [
    "BasicAuthSchema",
    "CreateBasicAuthSchema",
    "ReadBasicAuthSchema",
    "UpdateBasicAuthSchema",
    "CreateS3AuthSchema",
    "ReadS3AuthSchema",
    "S3AuthSchema",
    "UpdateS3AuthSchema",
    "CreateSambaAuthSchema",
    "ReadSambaAuthSchema",
    "SambaAuthSchema",
    "UpdateSambaAuthSchema",
    "AuthTokenSchema",
    "TokenPayloadSchema",
]
