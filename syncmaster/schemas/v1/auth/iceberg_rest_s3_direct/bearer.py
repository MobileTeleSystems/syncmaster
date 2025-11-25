# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import Field, SecretStr

from syncmaster.schemas.v1.auth.mixins import SecretDumpMixin


class ReadIcebergRESTCatalogBearerS3BasicAuthSchema(SecretDumpMixin):
    type: Literal["iceberg_rest_bearer_s3_basic"] = Field(description="Auth type")
    s3_access_key: str


class CreateIcebergRESTCatalogBearerS3BasicAuthSchema(ReadIcebergRESTCatalogBearerS3BasicAuthSchema):
    rest_catalog_token: SecretStr
    s3_secret_key: SecretStr


class UpdateIcebergRESTCatalogBearerS3BasicAuthSchema(ReadIcebergRESTCatalogBearerS3BasicAuthSchema):
    rest_catalog_token: SecretStr | None = None
    s3_secret_key: SecretStr | None = None

    def get_secret_fields(self) -> tuple[str, ...]:
        return ("rest_catalog_token", "s3_secret_key")
