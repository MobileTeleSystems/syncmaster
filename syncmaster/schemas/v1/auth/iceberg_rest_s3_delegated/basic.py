# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import BaseModel, Field, SecretStr


class ReadIcebergRESTCatalogBasicAuthSchema(BaseModel):
    type: Literal["iceberg_rest_basic"] = Field(description="Auth type")
    rest_catalog_username: str


class CreateIcebergRESTCatalogBasicAuthSchema(ReadIcebergRESTCatalogBasicAuthSchema):
    rest_catalog_password: SecretStr


class UpdateIcebergRESTCatalogBasicAuthSchema(ReadIcebergRESTCatalogBasicAuthSchema):
    rest_catalog_password: SecretStr | None = None

    def get_secret_fields(self) -> tuple[str, ...]:
        return ("rest_catalog_password",)
