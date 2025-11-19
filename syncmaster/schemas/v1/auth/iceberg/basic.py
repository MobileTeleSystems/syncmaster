# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import BaseModel, Field, SecretStr


class ReadIcebergRESTCatalogBasicAuthSchema(BaseModel):
    type: Literal["iceberg_rest_basic_s3_basic"] = Field(description="Auth type")
    rest_catalog_username: str
    s3_access_key: str


class CreateIcebergRESTCatalogBasicAuthSchema(ReadIcebergRESTCatalogBasicAuthSchema):
    rest_catalog_password: SecretStr
    s3_secret_key: SecretStr


class UpdateIcebergRESTCatalogBasicAuthSchema(ReadIcebergRESTCatalogBasicAuthSchema):
    rest_catalog_password: SecretStr | None = None
    s3_secret_key: SecretStr | None = None

    def get_secret_fields(self) -> tuple[str, ...]:
        return ("rest_catalog_password", "s3_secret_key")
