# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import Field

from syncmaster.settings import SyncmasterSettings


class SchedulerSettings(SyncmasterSettings):
    """Celery scheduler settings.

    Examples
    --------

    .. code-block:: bash

        SYNCMASTER__SCHEDULER__TRANSFER_FETCHING_TIMEOUT=200
    """

    TRANSFER_FETCHING_TIMEOUT_SECONDS: int = Field(
        180,
        description="Timeout for fetching transfers in seconds",
        alias="SCHEDULER__TRANSFER_FETCHING_TIMEOUT_SECONDS",
    )
    MISFIRE_GRACE_TIME_SECONDS: int = Field(
        300,
        description="Grace time for misfired jobs in seconds",
        alias="SCHEDULER__MISFIRE_GRACE_TIME_SECONDS",
    )
