# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, ByteSize, Field


class Resources(BaseModel):
    max_parallel_tasks: int = Field(1, ge=1, le=100, description="Parallel executors")
    cpu_cores_per_task: int = Field(1, ge=1, le=32, description="Cores per executor")
    ram_bytes_per_task: ByteSize = Field(
        1024**3,
        ge=512 * 1024**2,
        le=64 * 1024**3,
        description="RAM per executor",
    )
