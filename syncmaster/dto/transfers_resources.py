# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass


@dataclass
class Resources:
    max_parallel_tasks: int
    cpu_cores_per_task: int
    ram_bytes_per_task: int
