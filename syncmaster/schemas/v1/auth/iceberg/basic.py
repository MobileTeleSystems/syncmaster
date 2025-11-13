# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import BaseModel, SecretStr


class IcebergRESTCatalogBasicAuthSchema(BaseModel):
    type: Literal["iceberg_rest_basic_s3_basic"]


class CreateIcebergRESTCatalogBasicAuthSchema(IcebergRESTCatalogBasicAuthSchema):
    metastore_username: str
    metastore_password: SecretStr
    s3_access_key: str
    s3_secret_key: SecretStr


class ReadIcebergRESTCatalogBasicAuthSchema(IcebergRESTCatalogBasicAuthSchema):
    metastore_username: str
    s3_access_key: str


class UpdateIcebergRESTCatalogBasicAuthSchema(CreateIcebergRESTCatalogBasicAuthSchema):
    metastore_password: SecretStr | None = None
    s3_secret_key: SecretStr | None = None

    def get_secret_fields(self) -> tuple[str, ...]:
        return ("metastore_password", "s3_secret_key")
