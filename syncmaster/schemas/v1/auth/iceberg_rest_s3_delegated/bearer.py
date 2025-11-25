# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import Field, SecretStr

from syncmaster.schemas.v1.auth.mixins import SecretDumpMixin


class ReadIcebergRESTCatalogBearerAuthSchema(SecretDumpMixin):
    type: Literal["iceberg_rest_bearer"] = Field(description="Auth type")


class CreateIcebergRESTCatalogBearerAuthSchema(ReadIcebergRESTCatalogBearerAuthSchema):
    rest_catalog_token: SecretStr


class UpdateIcebergRESTCatalogBearerAuthSchema(ReadIcebergRESTCatalogBearerAuthSchema):
    rest_catalog_token: SecretStr | None = None

    def get_secret_fields(self) -> tuple[str, ...]:
        return ("rest_catalog_token",)
