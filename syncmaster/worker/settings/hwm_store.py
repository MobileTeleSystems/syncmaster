# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class HWMStoreSettings(BaseModel):
    """HWM Store settings.

    HWM Store is used for incremental strategy. See `etl-entities documentation <https://etl-entities.readthedocs.io/en/stable/hwm_store/base_hwm_store.html>`_.

    .. note::

        For now, the only supported HWMStore type for now is `Horizon <https://data-horizon.readthedocs.io/>`_.

    Examples
    --------

    .. code-block:: bash

        # Set the HWM Store connection URL
        SYNCMASTER__HWM_STORE__ENABLED=True
        SYNCMASTER__HWM_STORE__TYPE=horizon
        SYNCMASTER__HWM_STORE__URL=http://horizon:8000
        SYNCMASTER__HWM_STORE__USER=some_user
        SYNCMASTER__HWM_STORE__PASSWORD=changeme
        SYNCMASTER__HWM_STORE__NAMESPACE=syncmaster_internal
    """

    enabled: bool = Field(
        default=False,
        description="Enable or disable HWM Store",
    )
    type: Literal["horizon"] | None = Field(
        default=None,
        description="HWM Store type",
    )
    url: str | None = Field(
        default=None,
        description="HWM Store URL",
    )
    user: str | None = Field(
        default=None,
        description="HWM Store user",
    )
    password: str | None = Field(
        default=None,
        description="HWM Store password",
    )
    namespace: str | None = Field(
        default=None,
        description="HWM Store namespace",
    )

    @model_validator(mode="after")
    def check_required_fields_if_enabled(self):
        if self.enabled:
            missing_fields = [
                field for field in ("type", "url", "user", "password", "namespace") if getattr(self, field) is None
            ]
            if missing_fields:
                fields_str = ", ".join(missing_fields)
                msg = f"All fields must be set with enabled HWMStore. Missing: {fields_str}"
                raise ValueError(msg)
        return self
