# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import BaseModel, Field


class HWMStoreSettings(BaseModel):
    """HWM Store settings.

    HWM Store is used for incremental strategy. See `etl-entities documentation <https://etl-entities.readthedocs.io/en/stable/hwm_store/base_hwm_store.html>`_.

    Examples
    --------

    .. code-block:: bash

        # Set the HWM Store connection URL
        SYNCMASTER__HWM_STORE__URL=http://horizon:8000
    """

    type: Literal["horizon"] = Field(
        description=("HWM Store type"),
    )
    url: str = Field(
        description=("HWM Store URL"),
    )
    user: str = Field(
        description=("HWM Store user"),
    )
    password: str = Field(
        description=("HWM Store password"),
    )
    namespace: str = Field(
        description=("HWM Store namespace"),
    )
