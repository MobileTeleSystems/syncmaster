# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, ByteSize, Field

ONE_MB = 2**20  # noqa: WPS432
ONE_GB = 2**30  # noqa: WPS432


class Resources(BaseModel):
    max_parallel_tasks: int = Field(default=1, ge=1, le=100, description="Parallel executors")
    cpu_cores_per_task: int = Field(default=1, ge=1, le=32, description="Cores per executor")  # noqa: WPS432
    ram_bytes_per_task: ByteSize = Field(  # type: ignore[arg-type]
        default=ONE_GB,
        ge=512 * ONE_MB,  # noqa: WPS432
        le=64 * ONE_GB,  # noqa: WPS432
        description="RAM per executor",
    )
