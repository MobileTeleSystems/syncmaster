# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, ByteSize, Field


class Resources(BaseModel):
    max_parallel_tasks: int = Field(default=1, ge=1, le=100, description="Parallel executors")
    cpu_cores_per_task: int = Field(default=1, ge=1, le=32, description="Cores per executor")  # noqa: WPS432
    ram_bytes_per_task: ByteSize = Field(  # type: ignore[arg-type]
        default="1GiB",
        ge="512MiB",  # noqa: WPS432
        le="64GiB",  # noqa: WPS432
        description="RAM per executor",
    )
