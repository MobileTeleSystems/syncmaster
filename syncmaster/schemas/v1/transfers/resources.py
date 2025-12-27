# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, ByteSize, Field

ONE_MB = 2**20
ONE_GB = 2**30


class Resources(BaseModel):
    max_parallel_tasks: int = Field(default=1, ge=1, le=100, description="Parallel executors")
    cpu_cores_per_task: int = Field(default=1, ge=1, le=32, description="Cores per executor")
    ram_bytes_per_task: ByteSize = Field(  # type: ignore[assignment]
        default=ONE_GB,
        ge=512 * ONE_MB,
        le=64 * ONE_GB,
        description="RAM per executor",
    )
